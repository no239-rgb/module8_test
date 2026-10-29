# tests/e2e/conftest.py

import subprocess
import time
import pytest
from playwright.sync_api import sync_playwright
import requests

import subprocess
import time
import requests
import pytest

@pytest.fixture(scope="session", autouse=True)
def start_fastapi_server():
    # 1. Store the process instance in the 'process' variable
    process = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    server_url = "http://127.0.0.1:8000/"
    timeout = 30  # seconds
    start_time = time.time()
    server_up = False

    print("Starting FastAPI server...")

    while time.time() - start_time < timeout:
        # 2. Check if the process died prematurely
        if process.poll() is not None:
            _, stderr = process.communicate()
            raise RuntimeError(f"FastAPI server process died on startup:\n{stderr}")

        try:
            response = requests.get(server_url)
            if response.status_code < 500:
                server_up = True
                print("FastAPI server is up and running.")
                break
        except requests.exceptions.ConnectionError:
            pass

        time.sleep(1)

    if not server_up:
        process.kill()
        _, stderr = process.communicate()
        raise RuntimeError(
            f"FastAPI server failed to start within {timeout} seconds.\n"
            f"Server output log:\n{stderr}"
        )

    yield process

    # Terminate FastAPI server
    print("Shutting down FastAPI server...")
    process.terminate()
    process.wait()
    print("FastAPI server has been terminated.")

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
