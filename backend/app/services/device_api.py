"""厂商设备 API 服务 — 海康 ISAPI / 大华 CGI"""

import logging
import httpx

logger = logging.getLogger(__name__)


class HikvisionClient:
    """海康威视 ISAPI HTTP 接口"""

    @staticmethod
    async def check_alive(ip: str, port: int, username: str, password: str, timeout: int = 5) -> tuple[bool, int]:
        """检测海康设备是否在线

        Returns:
            (is_online, latency_ms)
        """
        url = f"http://{ip}:{port}/ISAPI/System/deviceInfo"
        try:
            async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
                resp = await client.get(url, auth=httpx.DigestAuth(username, password))
                latency = int(resp.elapsed.total_seconds() * 1000)
                # 任何 HTTP 响应都视为在线
                return True, latency
        except Exception as e:
            logger.debug("海康设备检测失败 %s:%s: %s", ip, port, e)
            return False, 0

    @staticmethod
    async def capture_snapshot(ip: str, port: int, channel: int, username: str, password: str, timeout: int = 10) -> bytes | None:
        """抓取海康设备快照

        Returns:
            JPEG 字节数据，失败返回 None
        """
        url = f"http://{ip}:{port}/ISAPI/Streaming/channels/{channel}01/picture"
        try:
            async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
                resp = await client.get(url, auth=httpx.DigestAuth(username, password))
                if resp.status_code == 200 and len(resp.content) > 100:
                    logger.info("海康快照成功 %s:%s ch=%s, size=%d", ip, port, channel, len(resp.content))
                    return resp.content
                logger.warning("海康快照失败 %s:%s ch=%s, status=%d", ip, port, channel, resp.status_code)
                return None
        except Exception as e:
            logger.warning("海康快照异常 %s:%s: %s", ip, port, e)
            return None

    @staticmethod
    def get_rtsp_url(ip: str, port: int, channel: int, username: str, password: str) -> str:
        """构造海康 RTSP 地址"""
        return f"rtsp://{username}:{password}@{ip}:554/Streaming/Channels/{channel}01"


class DahuaClient:
    """大华 CGI HTTP 接口"""

    @staticmethod
    async def check_alive(ip: str, port: int, username: str, password: str, timeout: int = 5) -> tuple[bool, int]:
        """检测大华设备是否在线

        Returns:
            (is_online, latency_ms)
        """
        url = f"http://{ip}:{port}/cgi-bin/magicBox.cgi?action=getSystemInfo"
        try:
            async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
                resp = await client.get(url, auth=httpx.BasicAuth(username, password))
                latency = int(resp.elapsed.total_seconds() * 1000)
                # 任何 HTTP 响应都视为在线
                return True, latency
        except Exception as e:
            logger.debug("大华设备检测失败 %s:%s: %s", ip, port, e)
            return False, 0

    @staticmethod
    async def capture_snapshot(ip: str, port: int, channel: int, username: str, password: str, timeout: int = 10) -> bytes | None:
        """抓取大华设备快照

        Returns:
            JPEG 字节数据，失败返回 None
        """
        url = f"http://{ip}:{port}/cgi-bin/snapshot.cgi?channel={channel}"
        try:
            async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
                resp = await client.get(url, auth=httpx.BasicAuth(username, password))
                if resp.status_code == 200 and len(resp.content) > 100:
                    logger.info("大华快照成功 %s:%s ch=%s, size=%d", ip, port, channel, len(resp.content))
                    return resp.content
                logger.warning("大华快照失败 %s:%s ch=%s, status=%d", ip, port, channel, resp.status_code)
                return None
        except Exception as e:
            logger.warning("大华快照异常 %s:%s: %s", ip, port, e)
            return None

    @staticmethod
    def get_rtsp_url(ip: str, port: int, channel: int, username: str, password: str) -> str:
        """构造大华 RTSP 地址"""
        return f"rtsp://{username}:{password}@{ip}:554/cam/realmonitor?channel={channel}&subtype=0"
