import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.request import Request, urlopen

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver

from tools.registry import register_tool


SITE_URL = "https://hswhds.com/"
API_BASE = "https://api.hswhds.com/api"
ALIYUN_CFT_MIRRORS = [
    "https://npmmirror.com/mirrors/chrome-for-testing",
    "https://registry.npmmirror.com/-/binary/chrome-for-testing",
]
OFFICIAL_CFT_MILESTONE_VERSIONS_URL = (
    "https://googlechromelabs.github.io/chrome-for-testing/"
    "latest-versions-per-milestone-with-downloads.json"
)

OUTPUT_COLUMNS = [
    "ID", "账号", "查询状态", "错误信息", "姓名", "证件号",
    "考生编号", "赛道", "组别", "报名时间", "市赛结果", "发证时间", "省赛", "国赛"
]


@register_tool('query_tools', '成绩查询', 'hswh_score', '华数华大成绩查询', '查询 hswhds.com 比赛成绩，支持单个和批量查询', icon='search')
class HswhScoreQuery:
    """华数华大成绩查询工具"""

    def __init__(self, driver_path: str = "", chrome_binary: str = ""):
        self.driver_path = driver_path
        self.chrome_binary = chrome_binary
        self._driver = None

    def _get_chrome_binary(self) -> str:
        if self.chrome_binary:
            return self.chrome_binary
        candidates = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
        for candidate in candidates:
            if Path(candidate).exists():
                return candidate
        return ""

    def _get_driver_path(self) -> str:
        if self.driver_path:
            return self.driver_path
        candidates = [
            "/usr/bin/chromedriver",
            "/usr/local/bin/chromedriver",
            "./chromedriver/chromedriver",
        ]
        for candidate in candidates:
            if Path(candidate).exists():
                return candidate
        return "chromedriver"

    def _make_driver(self, headless: bool = True) -> WebDriver:
        options = Options()
        options.page_load_strategy = "eager"
        binary = self._get_chrome_binary()
        if binary:
            options.binary_location = binary
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1440,1100")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--lang=zh-CN")

        service = Service(self._get_driver_path())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(20)
        return driver

    def _fetch_json(self, driver: WebDriver, path: str, payload: Optional[Dict[str, Any]], token: str = "") -> Dict[str, Any]:
        url = f"{API_BASE}{path}"
        script = """
            const [url, payload, token, done] = arguments;
            const headers = {
                "Content-Type": "application/json",
                "XX-Device-Type": "wxapp"
            };
            if (token) headers["XX-Token"] = token;
            fetch(url, {
                method: "POST",
                headers,
                body: JSON.stringify(payload || {})
            })
            .then(async response => {
                const text = await response.text();
                try {
                    done(JSON.parse(text));
                } catch (error) {
                    done({ code: -1, msg: "Invalid JSON response", raw: text });
                }
            })
            .catch(error => done({ code: -1, msg: String(error) }));
        """
        result = driver.execute_async_script(script, url, payload or {}, token)
        if not isinstance(result, dict):
            return {"code": -1, "msg": "Unexpected fetch result", "raw": result}
        return result

    def _login(self, driver: WebDriver, mobile: str, password: str) -> Dict[str, Any]:
        driver.get(SITE_URL)
        driver.execute_script("localStorage.clear(); sessionStorage.clear();")
        response = self._fetch_json(
            driver,
            "/user/login/login",
            {"mobile": mobile, "password": password, "isagree": 1},
        )
        if response.get("code") != 1:
            raise RuntimeError(response.get("msg") or f"登录失败: {response}")

        data = response.get("data") or {}
        token = data.get("token") or ""
        user_info = data.get("user_info") or {}
        if not token:
            raise RuntimeError(f"登录成功响应中没有 token: {response}")

        driver.execute_script(
            """
            localStorage.setItem('token', arguments[0]);
            localStorage.setItem('userInfo', JSON.stringify(arguments[1] || {}));
            """,
            token,
            user_info,
        )
        return {"token": token, "user_info": user_info}

    def _query_keyword(self, driver: WebDriver, keyword: str) -> List[Dict[str, Any]]:
        response = self._fetch_json(driver, "/home/index/query", {"keywords": keyword})
        if response.get("code") != 1:
            raise RuntimeError(response.get("msg") or f"查询失败: {response}")
        data = response.get("data") or []
        return data if isinstance(data, list) else [data]

    def _query_account_scores(self, driver: WebDriver, mobile: str, password: str) -> Dict[str, Any]:
        auth = self._login(driver, mobile, password)
        signup_response = self._fetch_json(driver, "/user/signup/index", {}, auth["token"])
        if signup_response.get("code") != 1:
            raise RuntimeError(signup_response.get("msg") or f"读取报名信息失败: {signup_response}")

        signups = (signup_response.get("data") or {}).get("list") or []
        results = []
        for signup in signups:
            signup_no = str(signup.get("signup_no") or "").strip()
            if not signup_no:
                results.append({"signup": signup, "score_results": []})
                continue
            results.append({
                "signup": signup,
                "score_results": self._query_keyword(driver, signup_no),
            })

        return {
            "user_info": auth.get("user_info") or {},
            "signups": signups,
            "results": results,
        }

    def _pick(self, record: Dict[str, Any], *keys: str, default: str = "") -> str:
        for key in keys:
            value = record.get(key)
            if value not in (None, ""):
                return str(value)
        return default

    def _pick_result(self, record: Dict[str, Any], *keys: str, default: str = "") -> str:
        value = self._pick(record, *keys, default="")
        return default if value in ("", "0", "None") else value

    def _flatten_results(self, data: Any) -> List[Dict[str, str]]:
        rows = []
        if isinstance(data, list):
            iterable = data
        else:
            iterable = data.get("results", []) if isinstance(data, dict) else []

        for item in iterable:
            if not isinstance(item, dict):
                continue
            if "score_results" in item:
                signup = item.get("signup") or {}
                score_results = item.get("score_results") or []
                if not score_results:
                    rows.append({
                        "姓名": "",
                        "证件号": "",
                        "考生编号": self._pick(signup, "signup_no"),
                        "赛道": self._pick(signup, "road_name"),
                        "组别": self._pick(signup, "groups_name"),
                        "报名时间": self._pick(signup, "time"),
                        "市赛结果": self._pick_result(signup, "has_prize_level_1", default="待公示"),
                        "发证时间": "",
                        "省赛": self._pick_result(signup, "has_prize_level_2", default="未开始"),
                        "国赛": self._pick_result(signup, "has_prize_level_3", default="未开始"),
                    })
                for score in score_results:
                    rows.extend(self._flatten_results([score]))
            else:
                rows.append({
                    "姓名": self._pick(item, "user_login", "name"),
                    "证件号": self._pick(item, "card_no"),
                    "考生编号": self._pick(item, "signup_no"),
                    "赛道": self._pick(item, "road_name"),
                    "组别": self._pick(item, "groups_name"),
                    "报名时间": self._pick(item, "time"),
                    "市赛结果": self._pick_result(item, "prize_level_1", "has_prize_level_1", default="待公示"),
                    "发证时间": self._pick(item, "prize_level_1_date"),
                    "省赛": self._pick_result(item, "prize_level_2", "has_prize_level_2", default="未开始"),
                    "国赛": self._pick_result(item, "prize_level_3", "has_prize_level_3", default="未开始"),
                })
        return rows

    def query_single(self, mobile: str, password: str) -> Dict[str, Any]:
        """查询单个账号成绩"""
        driver = self._make_driver()
        try:
            data = self._query_account_scores(driver, mobile, password)
            rows = self._flatten_results(data)
            return {
                "success": True,
                "user_info": data.get("user_info"),
                "results": rows,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            driver.quit()

    def query_by_keyword(self, keyword: str) -> Dict[str, Any]:
        """按编号查询"""
        driver = self._make_driver()
        try:
            driver.get(SITE_URL)
            data = self._query_keyword(driver, keyword)
            rows = self._flatten_results(data)
            return {
                "success": True,
                "results": rows,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            driver.quit()

    def query_batch(self, accounts: List[Dict[str, str]]) -> Dict[str, Any]:
        """批量查询"""
        driver = self._make_driver()
        all_results = []
        try:
            for i, account in enumerate(accounts, 1):
                mobile = account.get("account", "")
                password = account.get("password", "")
                account_id = account.get("id", str(i))

                if not mobile or not password:
                    all_results.append({
                        "ID": account_id,
                        "账号": mobile,
                        "查询状态": "失败",
                        "错误信息": "账号或密码为空",
                    })
                    continue

                try:
                    data = self._query_account_scores(driver, mobile, password)
                    rows = self._flatten_results(data)
                    for row in rows:
                        all_results.append({
                            "ID": account_id,
                            "账号": mobile,
                            "查询状态": "成功",
                            "错误信息": "",
                            **row,
                        })
                except Exception as e:
                    all_results.append({
                        "ID": account_id,
                        "账号": mobile,
                        "查询状态": "失败",
                        "错误信息": str(e),
                    })

            return {
                "success": True,
                "total": len(accounts),
                "results": all_results,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            driver.quit()
