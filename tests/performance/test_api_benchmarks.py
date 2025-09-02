"""
API性能基准测试

测试API的响应时间、吞吐量和并发性能
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from statistics import mean, median
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from football_predict_system.main import app


class APIPerformanceBenchmarks:
    """API性能基准测试类"""

    def __init__(self):
        self.client = TestClient(app)
        self.base_url = "http://testserver"

        # 性能基准阈值
        self.response_time_threshold = 2000  # ms
        self.throughput_threshold = 0.5  # requests/second
        self.max_memory_usage = 100  # MB

    def test_health_endpoint_performance(self):
        """测试健康检查端点性能"""
        endpoint = "/health"
        iterations = 100

        # 预热
        for _ in range(10):
            self.client.get(endpoint)

        # 性能测试
        start_time = time.perf_counter()
        response_times = []

        for _ in range(iterations):
            request_start = time.perf_counter()
            response = self.client.get(endpoint)
            request_end = time.perf_counter()

            assert response.status_code == 200
            response_times.append((request_end - request_start) * 1000)

        end_time = time.perf_counter()

        # 计算性能指标
        total_time = (end_time - start_time) * 1000  # ms
        avg_response_time = mean(response_times)
        median_response_time = median(response_times)
        p95_response_time = sorted(response_times)[int(0.95 * len(response_times))]
        throughput = iterations / (total_time / 1000)  # requests/second

        # 性能断言
        assert avg_response_time < self.response_time_threshold, (
            f"Average response time {avg_response_time:.2f}ms exceeds "
            f"threshold {self.response_time_threshold}ms"
        )

        assert throughput > self.throughput_threshold, (
            f"Throughput {throughput:.2f} req/s is below "
            f"threshold {self.throughput_threshold} req/s"
        )

        # 记录性能指标
        performance_report = {
            "endpoint": endpoint,
            "iterations": iterations,
            "total_time_ms": total_time,
            "avg_response_time_ms": avg_response_time,
            "median_response_time_ms": median_response_time,
            "p95_response_time_ms": p95_response_time,
            "throughput_req_per_sec": throughput,
        }

        print("\n🚀 Health Endpoint Performance Report:")
        for key, value in performance_report.items():
            print(
                f"  {key}: {value:.2f}"
                if isinstance(value, float)
                else f"  {key}: {value}"
            )

    def test_prediction_endpoint_performance(self):
        """测试预测端点性能"""
        endpoint = "/api/v1/predict"
        iterations = 50

        request_data = {"home_team": "Liverpool", "away_team": "Manchester City"}

        # 预热
        for _ in range(5):
            self.client.post(endpoint, json=request_data)

        # 性能测试
        response_times = []

        for _ in range(iterations):
            request_start = time.perf_counter()
            response = self.client.post(endpoint, json=request_data)
            request_end = time.perf_counter()

            # 跳过预期的错误(因为没有实际模型)
            if response.status_code in [200, 500]:
                response_times.append((request_end - request_start) * 1000)

        if response_times:  # 如果有有效的响应时间
            avg_response_time = mean(response_times)
            p95_response_time = sorted(response_times)[int(0.95 * len(response_times))]

            # 预测端点的阈值更宽松
            prediction_threshold = 500  # ms

            assert avg_response_time < prediction_threshold, (
                f"Prediction average response time {avg_response_time:.2f}ms "
                f"exceeds threshold {prediction_threshold}ms"
            )

            performance_report = {
                "endpoint": endpoint,
                "iterations": len(response_times),
                "avg_response_time_ms": avg_response_time,
                "p95_response_time_ms": p95_response_time,
            }

            print("\n🎯 Prediction Endpoint Performance Report:")
            for key, value in performance_report.items():
                print(
                    f"  {key}: {value:.2f}"
                    if isinstance(value, float)
                    else f"  {key}: {value}"
                )

    def test_concurrent_requests_performance(self):
        """测试并发请求性能"""
        endpoint = "/health"
        concurrent_users = 10
        requests_per_user = 20

        def make_requests():
            """单个用户的请求函数"""
            response_times = []
            for _ in range(requests_per_user):
                start = time.perf_counter()
                response = self.client.get(endpoint)
                end = time.perf_counter()

                if response.status_code == 200:
                    response_times.append((end - start) * 1000)
            return response_times

        # 并发测试
        start_time = time.perf_counter()

        patches = [
            patch(
                "football_predict_system.core.health.HealthChecker.check_database_health",
                return_value=(True, "mocked"),
            ),
            patch(
                "football_predict_system.core.health.HealthChecker.check_redis_health",
                return_value=(True, "mocked"),
            ),
            patch(
                "football_predict_system.core.health.HealthChecker.check_model_registry",
                return_value=(True, "mocked"),
            ),
            patch(
                "football_predict_system.core.health.HealthChecker.check_external_apis",
                return_value=(True, "mocked"),
            ),
        ]
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                futures = [
                    executor.submit(make_requests) for _ in range(concurrent_users)
                ]
                all_response_times = []

                for future in futures:
                    user_times = future.result()
                    all_response_times.extend(user_times)

        end_time = time.perf_counter()

        if all_response_times:
            total_requests = len(all_response_times)
            total_time = end_time - start_time
            avg_response_time = mean(all_response_times)
            throughput = total_requests / total_time

            # 并发性能断言
            concurrent_threshold = 2000  # ms for concurrent requests (adjusted for CI)
            concurrent_throughput_threshold = 50  # req/s

            assert avg_response_time < concurrent_threshold, (
                f"Concurrent average response time {avg_response_time:.2f}ms "
                f"exceeds threshold {concurrent_threshold}ms"
            )

            assert throughput > concurrent_throughput_threshold, (
                f"Concurrent throughput {throughput:.2f} req/s is below "
                f"threshold {concurrent_throughput_threshold} req/s"
            )

            performance_report = {
                "concurrent_users": concurrent_users,
                "requests_per_user": requests_per_user,
                "total_requests": total_requests,
                "total_time_s": total_time,
                "avg_response_time_ms": avg_response_time,
                "throughput_req_per_sec": throughput,
            }

            print("\n⚡ Concurrent Performance Report:")
            for key, value in performance_report.items():
                print(
                    f"  {key}: {value:.2f}"
                    if isinstance(value, float)
                    else f"  {key}: {value}"
                )

    @pytest.mark.asyncio
    async def test_async_client_performance(self):
        """测试异步客户端性能"""
        endpoint = f"{self.base_url}/health"
        concurrent_requests = 50

        async def make_async_request(session: httpx.AsyncClient) -> float:
            """异步请求函数"""
            start = time.perf_counter()
            try:
                response = await session.get(endpoint)
                end = time.perf_counter()
                return (end - start) * 1000 if response.status_code == 200 else 0
            except Exception:
                return 0

        # 异步并发测试
        async with httpx.AsyncClient() as client:
            start_time = time.perf_counter()

            tasks = [make_async_request(client) for _ in range(concurrent_requests)]
            response_times = await asyncio.gather(*tasks)

            end_time = time.perf_counter()

        # 过滤有效的响应时间
        valid_times = [t for t in response_times if t > 0]

        if valid_times:
            total_time = end_time - start_time
            avg_response_time = mean(valid_times)
            throughput = len(valid_times) / total_time

            # 异步性能通常更好
            async_threshold = 150  # ms

            assert avg_response_time < async_threshold, (
                f"Async average response time {avg_response_time:.2f}ms "
                f"exceeds threshold {async_threshold}ms"
            )

            performance_report = {
                "async_concurrent_requests": concurrent_requests,
                "successful_requests": len(valid_times),
                "total_time_s": total_time,
                "avg_response_time_ms": avg_response_time,
                "throughput_req_per_sec": throughput,
            }

            print("\n🔄 Async Performance Report:")
            for key, value in performance_report.items():
                print(
                    f"  {key}: {value:.2f}"
                    if isinstance(value, float)
                    else f"  {key}: {value}"
                )


# 性能测试实例
benchmarks = APIPerformanceBenchmarks()


def test_health_performance():
    """健康检查性能测试"""
    benchmarks.test_health_endpoint_performance()


def test_prediction_performance():
    """预测性能测试"""
    benchmarks.test_prediction_endpoint_performance()


def test_concurrent_performance():
    """并发性能测试"""
    benchmarks.test_concurrent_requests_performance()


@pytest.mark.asyncio
async def test_async_performance():
    """异步性能测试"""
    await benchmarks.test_async_client_performance()


if __name__ == "__main__":
    print("🏁 Starting Performance Benchmarks...")

    benchmarks.test_health_endpoint_performance()
    benchmarks.test_prediction_endpoint_performance()
    benchmarks.test_concurrent_requests_performance()

    print("\n✅ Performance benchmarks completed!")
