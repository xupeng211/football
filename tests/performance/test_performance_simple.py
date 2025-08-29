"""
性能和负载测试
"""
import time

import numpy as np
import pandas as pd
import pytest


class TestPredictionPerformance:
    """预测性能测试"""

    def test_single_prediction_performance(self):
        """测试单次预测性能"""
        try:
            from models.predictor import _create_feature_vector

            # 测试数据
            test_data = {
                "home_odds": 2.0,
                "draw_odds": 3.0,
                "away_odds": 4.0
            }

            # 性能测试
            start_time = time.time()

            for _ in range(100):
                result = _create_feature_vector(test_data)
                assert len(result) == 1

            end_time = time.time()
            duration = end_time - start_time

            # 验证性能要求: 100次预测应在2秒内完成
            assert duration < 2.0, f"Performance too slow: {duration:.3f}s"

            # 计算每秒预测数
            predictions_per_second = 100 / duration
            assert predictions_per_second > 50, f"Too slow: {predictions_per_second:.1f}"

        except ImportError:
            pytest.skip("Predictor module not available")

    def test_batch_prediction_scalability(self):
        """测试批量预测可扩展性"""
        try:
            from models.predictor import _create_feature_vector

            # 测试不同批量大小的性能
            batch_sizes = [1, 10, 50, 100]
            performance_results = {}

            test_data = {
                "home_odds": 2.0,
                "draw_odds": 3.0,
                "away_odds": 4.0
            }

            for batch_size in batch_sizes:
                start_time = time.time()

                for _ in range(batch_size):
                    result = _create_feature_vector(test_data)
                    assert len(result) == 1

                end_time = time.time()
                duration = end_time - start_time
                performance_results[batch_size] = duration

            # 验证性能线性扩展
            for i, batch_size in enumerate(batch_sizes[1:], 1):
                prev_batch = batch_sizes[i-1]

                # 计算平均每次预测时间
                avg_time_prev = performance_results[prev_batch] / prev_batch
                avg_time_curr = performance_results[batch_size] / batch_size

                # 性能退化不应超过100%
                assert avg_time_curr < avg_time_prev * 2.0, \
                    f"Performance degraded: {avg_time_curr:.6f}s vs {avg_time_prev:.6f}s"

        except ImportError:
            pytest.skip("Predictor module not available")

    def test_concurrent_prediction_performance(self):
        """测试并发预测性能"""
        import concurrent.futures

        def prediction_task(task_id):
            """单个预测任务"""
            try:
                from models.predictor import _create_feature_vector

                test_data = {
                    "home_odds": 2.0,
                    "draw_odds": 3.0,
                    "away_odds": 4.0
                }

                start_time = time.time()
                result = _create_feature_vector(test_data)
                end_time = time.time()

                return {
                    "task_id": task_id,
                    "duration": end_time - start_time,
                    "success": len(result) == 1
                }
            except Exception as e:
                return {"task_id": task_id, "error": str(e), "success": False}

        # 测试并发执行
        num_tasks = 10
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(prediction_task, i) for i in range(num_tasks)]
            results = [future.result() for future in futures]

        total_duration = time.time() - start_time

        # 验证所有任务成功
        successful_tasks = [r for r in results if r.get("success", False)]
        assert len(successful_tasks) >= num_tasks * 0.8  # 至少80%成功

        # 验证并发性能
        if len(successful_tasks) > 0:
            sequential_estimate = sum(r["duration"] for r in successful_tasks)
            speedup_ratio = sequential_estimate / total_duration

            # 至少应该有一些并发提升
            assert speedup_ratio > 1.0, f"Poor concurrency: {speedup_ratio:.2f}x"


class TestDataProcessingPerformance:
    """数据处理性能测试"""

    def test_feature_engineering_performance(self):
        """测试特征工程性能"""
        try:
            from data_pipeline.transforms.feature_engineer import (
                calculate_implied_probabilities,
            )

            # 创建大数据集进行测试
            large_dataset_size = 1000
            df = pd.DataFrame({
                'home_odds': np.random.uniform(1.5, 4.0, large_dataset_size),
                'draw_odds': np.random.uniform(2.5, 4.5, large_dataset_size),
                'away_odds': np.random.uniform(1.5, 6.0, large_dataset_size)
            })

            # 性能测试
            start_time = time.time()
            result = calculate_implied_probabilities(df)
            end_time = time.time()
            duration = end_time - start_time

            # 验证结果正确性
            assert len(result) == large_dataset_size
            assert 'implied_prob_home' in result.columns

            # 验证性能: 1000行数据应在0.1秒内处理完成
            assert duration < 0.1, f"Feature engineering too slow: {duration:.3f}s"

        except ImportError:
            pytest.skip("Feature engineering module not available")

    def test_dataframe_operations_performance(self):
        """测试DataFrame操作性能"""
        large_size = 10000

        # 创建大型DataFrame
        start_time = time.time()
        df = pd.DataFrame({
            'team_id': range(large_size),
            'score': np.random.randint(0, 5, large_size),
            'odds': np.random.uniform(1.0, 10.0, large_size)
        })

        # 执行复杂操作
        filtered_df = df[df['score'] > 2]
        grouped_df = df.groupby('score').agg({'odds': ['mean', 'max', 'min']})
        sorted_df = df.sort_values(['score', 'odds'])

        end_time = time.time()
        duration = end_time - start_time

        # 验证操作正确性
        assert len(filtered_df) > 0
        assert len(grouped_df) > 0
        assert len(sorted_df) == large_size

        # 性能要求: 10K行数据操作应在1秒内完成
        assert duration < 1.0, f"DataFrame operations too slow: {duration:.3f}s"

    def test_memory_usage_efficiency(self):
        """测试内存使用效率"""
        try:
            import gc

            import psutil

            # 记录初始内存使用
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # 创建大量数据
            large_data = []
            for i in range(10000):
                large_data.append({
                    'id': i,
                    'data': np.random.random(100).tolist()
                })

            # 记录峰值内存使用
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB

            # 清理数据
            del large_data
            gc.collect()

            memory_increase = peak_memory - initial_memory

            # 验证内存使用合理(不应超过100MB增长)
            assert memory_increase < 100, f"Memory usage too high: {memory_increase:.1f}MB"

        except ImportError:
            pytest.skip("psutil not available for memory testing")


if __name__ == "__main__":
    pytest.main([__file__])
