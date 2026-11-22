"""Real browser smoke test using an isolated headless Chrome profile and original sample material."""
import base64
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
from uuid import uuid4
from websockets.sync.client import connect

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/"data"/"browser-qa"
QA.mkdir(parents=True,exist_ok=True)
BROWSER=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",0))
        return sock.getsockname()[1]


def fetch(url):
    with urllib.request.urlopen(url,timeout=2) as response:
        return response.read()


def run():
    port,debug=free_port(),free_port()
    url=f"http://127.0.0.1:{port}"
    server=browser=None
    ws=None
    log=(QA/"server.log").open("w",encoding="utf-8")
    try:
        environment={**os.environ,"LLM_PROVIDER":"demo","ALLOW_PAID_API":"false","EMBEDDING_BACKEND":"local",
                     "REQUIRE_PASSWORD":"false","DATA_DIR":str(QA/"private-data")}
        server=subprocess.Popen([sys.executable,"-m","streamlit","run","app.py","--server.port",str(port)],
                                cwd=ROOT,env=environment,stdout=log,stderr=subprocess.STDOUT,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        deadline=time.monotonic()+40
        while time.monotonic()<deadline:
            try:
                if fetch(url+"/_stcore/health")==b"ok":
                    break
            except Exception:
                time.sleep(.25)
        else:
            raise RuntimeError("Server health timed out")
        assert b"<html" in fetch(url).lower()
        print("HTTP and health endpoint: passed",flush=True)
        browser=subprocess.Popen([str(BROWSER),"--headless=new","--disable-gpu","--no-first-run",
            "--no-default-browser-check","--remote-debugging-address=127.0.0.1",
            f"--remote-debugging-port={debug}",f"--user-data-dir={QA / ('profile-'+uuid4().hex)}","about:blank"],
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            try:
                pages=json.loads(fetch(f"http://127.0.0.1:{debug}/json"))
                target=next(page for page in pages if page["type"]=="page")
                break
            except Exception:
                time.sleep(.25)
        else:
            raise RuntimeError("Browser did not start")
        ws=connect(target["webSocketDebuggerUrl"],max_size=20_000_000,legacy=True)
        counter=0
        def command(method,params=None):
            nonlocal counter
            counter+=1
            request=counter
            ws.send(json.dumps({"id":request,"method":method,"params":params or {}}))
            while True:
                reply=json.loads(ws.recv(timeout=20))
                if reply.get("id")==request:
                    if "error" in reply:
                        raise RuntimeError(reply["error"])
                    return reply.get("result",{})
        def evaluate(expression):
            result=command("Runtime.evaluate",{"expression":expression,"returnByValue":True})
            if "exceptionDetails" in result:
                raise RuntimeError(result["exceptionDetails"])
            return result.get("result",{}).get("value")
        def wait_for(expression,timeout=30):
            deadline=time.monotonic()+timeout
            while time.monotonic()<deadline:
                if evaluate(expression):
                    return
                time.sleep(.2)
            raise RuntimeError("Browser condition timed out: "+expression)
        def wait_text(text):
            wait_for("document.body.innerText.includes("+json.dumps(text)+")")
        def click_text(text,selector="button"):
            expression="[...document.querySelectorAll("+json.dumps(selector)+")].find(e=>e.innerText.trim()==="+json.dumps(text)+")"
            if text == "Clear chat":
                expression="[...document.querySelectorAll("+json.dumps(selector)+")].find(e=>e.innerText.includes("+json.dumps(text)+"))"
            wait_for("!!("+expression+")")
            evaluate(expression+".click()")
            time.sleep(.4)
        def fill(label,value):
            expression="[...document.querySelectorAll('[data-testid=\"stTextInput\"]')].find(e=>e.innerText.includes("+json.dumps(label)+")).querySelector('input')"
            evaluate(expression+".focus()")
            command("Input.insertText",{"text":value})
            command("Input.dispatchKeyEvent",{"type":"keyDown","key":"Tab","code":"Tab","windowsVirtualKeyCode":9})
            command("Input.dispatchKeyEvent",{"type":"keyUp","key":"Tab","code":"Tab","windowsVirtualKeyCode":9})
            time.sleep(.5)
        def chat(question):
            wait_for("!!document.querySelector('[data-testid=\"stChatInput\"] textarea')")
            evaluate("document.querySelector('[data-testid=\"stChatInput\"] textarea').focus()")
            command("Input.insertText",{"text":question})
            command("Input.dispatchKeyEvent",{"type":"keyDown","key":"Enter","code":"Enter","windowsVirtualKeyCode":13})
            command("Input.dispatchKeyEvent",{"type":"keyUp","key":"Enter","code":"Enter","windowsVirtualKeyCode":13})
        def screenshot(name):
            image=command("Page.captureScreenshot",{"format":"png","captureBeyondViewport":False})
            (QA/name).write_bytes(base64.b64decode(image["data"]))
        command("Page.enable")
        command("Runtime.enable")
        command("Emulation.setDeviceMetricsOverride",{"width":1440,"height":1100,"deviceScaleFactor":1,"mobile":False})
        command("Page.navigate",{"url":url})
        wait_text("Your CA study space.")
        wait_text("Demo mode")
        assert not evaluate("!!document.querySelector('[data-testid=\"stException\"]')")
        wait_for("!!document.querySelector('[data-testid=\"stChatInput\"] textarea')")
        time.sleep(.5)
        screenshot("desktop.png")
        chat("Annual straight-line depreciation: cost 850000, residual value 50000, useful life 8 years.")
        wait_text("Depreciation for the stated period: INR 100000.00.")
        screenshot("calculation.png")
        print("Natural-language changed-value calculation: passed",flush=True)
        click_text("Clear chat")
        wait_text("Start with the question on your mind")
        fill("Examination attempt","May 2027")
        click_text("Study library",'[role="tab"]')
        evaluate("[...document.querySelectorAll('[data-testid=\"stCheckbox\"]')].find(e=>e.innerText.includes('I have permission')).querySelector('input').click()")
        wait_for("!document.querySelector('input[type=\"file\"]').disabled")
        fill("Document title","Original QA depreciation notes")
        document=command("DOM.getDocument")
        node=command("DOM.querySelector",{"nodeId":document["root"]["nodeId"],"selector":"input[type=file]"})
        command("DOM.setFileInputFiles",{"nodeId":node["nodeId"],"files":[str(ROOT/"data"/"sample-depreciation.pdf")]})
        wait_for("[...document.querySelectorAll('button')].some(b=>b.innerText.trim()==='Process and index PDF'&&!b.disabled)")
        click_text("Process and index PDF")
        wait_text("Indexed 1 readable pages")
        print("Authorized PDF ingestion: passed",flush=True)
        click_text("Study chat",'[role="tab"]')
        chat("Explain residual value.")
        wait_text("Retrieved passages")
        wait_text("[S1]")
        assert not evaluate("!!document.querySelector('[data-testid=\"stException\"]')")
        screenshot("retrieval.png")
        downloads=QA/("downloads-"+uuid4().hex)
        downloads.mkdir()
        command("Browser.setDownloadBehavior",{"behavior":"allow","downloadPath":str(downloads)})
        wait_for("document.body.innerText.includes('Download chat')")
        evaluate("[...document.querySelectorAll('*')].find(e=>e.children.length===0&&typeof e.innerText==='string'&&e.innerText.trim()==='Download chat')?.closest('button, a')?.click()")
        deadline=time.monotonic()+10
        while time.monotonic()<deadline and not list(downloads.glob("*.json")):
            time.sleep(.2)
        exported=json.loads(next(downloads.glob("*.json")).read_text(encoding="utf-8"))
        assert exported["messages"][-1]["sources"][0]["metadata"]["title"]=="Original QA depreciation notes"
        print("Scoped retrieval, source reference and chat download: passed",flush=True)
        click_text("Clear chat")
        wait_text("Start with the question on your mind")
        command("Emulation.setDeviceMetricsOverride",{"width":390,"height":844,"deviceScaleFactor":1,"mobile":True})
        time.sleep(.5)
        evaluate("document.querySelector('[data-testid=\"stSidebarCollapseButton\"] button')?.click()")
        time.sleep(.3)
        assert evaluate("document.documentElement.scrollWidth<=window.innerWidth+1")
        screenshot("mobile.png")
        print("390px mobile viewport: passed",flush=True)
        (QA/"result.json").write_text(json.dumps({"http":True,"calculation":True,"pdf_ingestion":True,
            "retrieval":True,"download":True,"mobile":True,"live_api":False},indent=2))
        command("Browser.close")
    finally:
        if ws:
            ws.close()
        if browser:
            try:
                browser.wait(timeout=5)
            except subprocess.TimeoutExpired:
                browser.terminate()
        if server:
            subprocess.run(["taskkill","/PID",str(server.pid),"/T","/F"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        log.close()


if __name__=="__main__":
    run()
