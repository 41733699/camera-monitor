"""ONVIF 心跳探测器 — GetSystemDateAndTime 轻量检测

原理：向摄像头 ONVIF 服务发送 GetSystemDateAndTime SOAP 请求。
这是 ONVIF 协议中最轻量的接口，不需要认证，仅验证设备 ONVIF 服务是否存活。

典型耗时：50~200ms（vs ffprobe 的 3000~5000ms）
"""

import socket
import time
import logging
import http.client

logger = logging.getLogger(__name__)

# SOAP 请求体（ONVIF 标准，不需要认证）
ONVIF_GET_TIME_SOAP = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope
    xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
    xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
    <soap:Body>
        <tds:GetSystemDateAndTime/>
    </soap:Body>
</soap:Envelope>"""


def check_onvif(domain: str, port: int = 80, timeout: int = 5, path: str = "/onvif/device_service") -> tuple[bool, int]:
    """
    ONVIF GetSystemDateAndTime 心跳检测。

    Args:
        domain: 摄像头 IP 或域名
        port: ONVIF 端口
        timeout: 超时秒数
        path: ONVIF 服务路径

    Returns:
        (is_online: bool, latency_ms: int)
    """
    try:
        t0 = time.time()

        conn = http.client.HTTPConnection(domain, port, timeout=timeout)
        conn.request(
            "POST",
            path,
            body=ONVIF_GET_TIME_SOAP,
            headers={
                "Content-Type": "application/soap+xml; charset=utf-8",
                "Connection": "close",
            },
        )
        resp = conn.getresponse()
        body = resp.read()
        conn.close()

        latency = int((time.time() - t0) * 1000)

        # 只要设备返回了 HTTP 响应（任何状态码），就说明设备是存活的
        return True, latency

    except socket.timeout:
        return False, 0
    except ConnectionRefusedError:
        return False, 0
    except OSError as e:
        logger.debug("ONVIF 检测失败 %s:%d: %s", domain, port, e)
        return False, 0
    except Exception as e:
        logger.warning("ONVIF 检测异常 %s:%d: %s", domain, port, e)
        return False, 0
