# tests/e2e/conftest.py

import os
import sys
import time
import subprocess
import requests
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session", autouse=True)
def start_fastapi_server():
    # Pass PYTHONPATH so Uvicorn can import modules from the root directory
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(".")

    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )

    server_url = "http://127.0.0.1:8000/"
    timeout = 30
    start_time = time.time()
    server_up = False

    print("Starting FastAPI server...")

    while time.time() - start_time < timeout:
        if process.poll() is not None:
            _, stderr = process.communicate()
            raise RuntimeError(f"FastAPI server process died on startup:\n{stderr}")

        try:
            # timeout=2 stops requests.get from hanging CI indefinitely if connection stalls
            response = requests.get(server_url, timeout=2)
            if response.status_code < 500:
                server_up = True
                print("FastAPI server is up and running.")
                break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pass

        time.sleep(1)

    if not server_up:
        process.kill()
        _, stderr = process.communicate()
        raise RuntimeError(f"FastAPI server failed to start within {timeout}s:\n{stderr}")

    yield process

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()

@pytest.fixture(scope="session")
def playwright_instance_fixture():
    """
    Fixture to manage Playwright's lifecycle.
    """
    with sync_playwright() as p:
        yield p

@pytest.fixture(scope="session")
def browser(playwright_instance_fixture):
    """
    Fixture to launch a browser instance.
    """
    browser = playwright_instance_fixture.chromium.launch(headless=True)
    yield browser
    browser.close()

@pytest.fixture(scope="function")
def page(browser):
    """
    Fixture to create a new page for each test.
    """
    page = browser.new_page()
    yield page
    page.close()
