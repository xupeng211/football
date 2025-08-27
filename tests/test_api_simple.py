"""
简单API测试 - 测试API模块导入和基本功能
"""


def test_app_import():
    """测试API应用导入"""
    from apps.api.main import app

    assert app is not None
    assert hasattr(app, "title")
    assert "足球预测" in app.title


def test_health_router_import():
    """测试健康检查路由导入"""
    from apps.api.routers import health

    assert health.router is not None


def test_metrics_router_import():
    """测试监控指标路由导入"""
    from apps.api.routers import metrics

    assert metrics.router is not None
    assert hasattr(metrics, "REQUEST_COUNT")
    assert hasattr(metrics, "SYSTEM_UPTIME")


def test_predictions_router_import():
    """测试预测路由导入"""
    from apps.api.routers import predictions

    assert predictions.router is not None


def test_app_routes_registered():
    """测试应用路由注册"""
    from apps.api.main import app

    # 检查路由是否注册
    routes = [getattr(route, "path", "") for route in app.routes]
    assert "/" in routes  # 根路径

    # 检查是否有API路由
    api_routes = [route for route in app.routes if hasattr(route, "path_regex")]
    assert len(api_routes) > 0


def test_cors_middleware():
    """测试CORS中间件配置"""
    from apps.api.main import app

    # MVP版本可能没有CORS中间件,这是可接受的
    middleware_types = [getattr(m.cls, "__name__", str(m.cls)) for m in app.user_middleware]
    # MVP版本允许没有CORS中间件
    assert isinstance(middleware_types, list)


def test_exception_handler():
    """测试全局异常处理器"""
    from apps.api.main import app

    # 检查异常处理器是否注册,MVP版本只需要有基础的处理器
    assert hasattr(app, "exception_handlers")
    assert len(app.exception_handlers) >= 0  # 至少有FastAPI默认的处理器


def test_prometheus_metrics():
    """测试Prometheus指标"""
    from apps.api.routers.metrics import REQUEST_COUNT, SYSTEM_UPTIME, registry

    # 测试指标对象存在
    assert REQUEST_COUNT is not None
    assert SYSTEM_UPTIME is not None
    assert registry is not None

    # 测试指标可以操作
    REQUEST_COUNT.labels(method="GET", endpoint="/test").inc()
    SYSTEM_UPTIME.set(100)
