# AI-Fix-Enhancement: Added for Regression testing framework
# BUGFIX: Example for a division by zero error [2025-08-31/Cascade]

import pytest


# 假设我们有一个函数,在过去的某个版本中存在bug
def calculate_ratio(a, b):
    """
    一个简单的计算函数,在早期版本中,当 b 为 0 时会导致程序崩溃。
    修复方案是当 b 为 0 时,返回一个安全的值(例如0)。
    """
    if b == 0:
        return 0  # 这是针对bug的修复
    return a / b


@pytest.mark.regression
def test_regression_div_by_zero():
    """
    回归测试:确保`calculate_ratio`函数在分母为0时不会崩溃。

    这个测试用例专门用于验证一个已经修复的bug,防止它在未来的代码变更中再次出现。
    """
    # Arrange: 准备一个会导致旧bug触发的场景
    numerator = 10
    denominator = 0

    # Act: 调用函数,并捕获任何可能的异常
    try:
        result = calculate_ratio(numerator, denominator)
    except ZeroDivisionError:
        # 如果程序因为 ZeroDivisionError 而崩溃,测试就失败
        pytest.fail(
            "REGRESSION: The division by zero bug has reappeared in calculate_ratio()"
        )

    # Assert: 验证函数的行为是否符合修复后的预期
    assert result == 0, "The function should return 0 when denominator is zero"


@pytest.mark.regression
def test_regression_normal_case():
    """
    回归测试:确保修复方案没有破坏正常的函数功能。
    """
    # Arrange
    numerator = 10
    denominator = 2

    # Act
    result = calculate_ratio(numerator, denominator)

    # Assert
    assert result == 5
