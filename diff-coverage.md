# Diff Coverage
## Diff: origin/main...HEAD, staged and unstaged changes

- apps/api/core/settings&#46;py (100%)
- apps/api/main&#46;py (93.3%): Missing lines 175
- apps/api/routers/health&#46;py (80.0%): Missing lines 83
- apps/api/routers/predictions&#46;py (100%)
- apps/backtest/engine&#46;py (87.5%): Missing lines 298
- apps/trainer/xgboost_trainer&#46;py (30.0%): Missing lines 118,125,243,258,260,275,283
- apps/workers/flows/data_collection_flow&#46;py (80.0%): Missing lines 314
- data_pipeline/features/build&#46;py (65.9%): Missing lines 103,106,140,152,258,260,268,273-274,280,282,286,324,328
- data_pipeline/features/rolling&#46;py (100%)
- data_pipeline/ingest/base&#46;py (100%)
- data_pipeline/ingest/csv_adapter&#46;py (50.0%): Missing lines 63,123
- data_pipeline/sources/football_api&#46;py (100%)
- data_pipeline/sources/ingest_odds&#46;py (80.0%): Missing lines 102
- data_pipeline/sources/odds_fetcher&#46;py (100%)
- data_pipeline/transforms/ingest_features&#46;py (100%)
- models/predictor&#46;py (84.3%): Missing lines 90,102,144,146,161-162,175-176
- models/registry&#46;py (83.3%): Missing lines 253
- trainer/fit_xgb&#46;py (60.0%): Missing lines 63,193

## Summary

- **Total**: 187 lines
- **Missing**: 39 lines
- **Coverage**: 79%



## apps/api/main&#46;py

Lines 171-176

```python
  171
  172
  173 if __name__ == "__main__":
  174     # 开发模式运行
! 175     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)  # nosec B104
```


---



## apps/api/routers/health&#46;py

Lines 79-84

```python
  79         )
  80
  81     except Exception as e:
  82         logger.error("健康检查失败", exc=str(e))
! 83         raise HTTPException(status_code=503, detail="健康检查失败") from e
```


---



## apps/backtest/engine&#46;py

Lines 294-302

```python
  294         away_score = row.get("away_score", 0)
  295
  296         # 如果没有比分数据,生成随机结果用于演示
  297         if pd.isna(home_score) or pd.isna(away_score):
! 298             return int(np.random.choice([0, 1, 2]))  # 随机结果
  299
  300         if home_score > away_score:
  301             return 2  # 主胜
  302         elif home_score == away_score:
```


---



## apps/trainer/xgboost_trainer&#46;py

Lines 114-122

```python
  114         """验证数据质量"""
  115         # 检查空值
  116         null_counts = features.isnull().sum()
  117         if null_counts.sum() > 0:
! 118             logger.warning(
  119                 "发现空值", null_features=null_counts[null_counts > 0].to_dict()
  120             )
  121
  122         # 检查无穷值
```


---


Lines 121-129

```python
  121
  122         # 检查无穷值
  123         inf_counts = np.isinf(features.select_dtypes(include=[np.number])).sum()
  124         if inf_counts.sum() > 0:
! 125             logger.warning(
  126                 "发现无穷值", inf_features=inf_counts[inf_counts > 0].to_dict()
  127             )
  128
  129         # 检查目标变量分布
```


---


Lines 239-247

```python
  239         Returns:
  240             预测概率 (n_samples, 3) - [客胜概率, 平局概率, 主胜概率]
  241         """
  242         if self.model is None:
! 243             raise ValueError("模型未训练, 请先调用train()方法")
  244
  245         return self.model.predict_proba(features)
  246
  247     def predict(self, features: pd.DataFrame) -> np.ndarray[Any, Any]:
```


---


Lines 254-264

```python
  254         Returns:
  255             预测类别 (0: 客胜, 1: 平局, 2: 主胜)
  256         """
  257         if self.model is None:
! 258             raise ValueError("模型未训练, 请先调用train()方法")
  259
! 260         return self.model.predict(features)  # type: ignore[no-any-return]
  261
  262     def get_feature_importance(self, top_k: int = 20) -> dict[str, float]:
  263         """
  264         获取特征重要性
```


---


Lines 271-279

```python
  271         """
  272         if self.model is None:
  273             raise ValueError("模型未训练")
  274
! 275         importance = dict(
  276             zip(
  277                 self.feature_names,
  278                 self.model.feature_importances_,
  279                 strict=False,
```


---


Lines 279-287

```python
  279                 strict=False,
  280             )
  281         )
  282         # 按重要性降序排列
! 283         sorted_importance = dict(
  284             sorted(importance.items(), key=lambda x: x[1], reverse=True)
  285         )
  286
  287         return dict(list(sorted_importance.items())[:top_k])
```


---



## apps/workers/flows/data_collection_flow&#46;py

Lines 310-318

```python
  310 if __name__ == "__main__":
  311     import asyncio
  312
  313     # 测试运行
! 314     async def test_flow() -> None:
  315         result = await daily_data_collection_flow()
  316         print(f"Flow result: {result}")
  317
  318     asyncio.run(test_flow())
```


---



## data_pipeline/features/build&#46;py

Lines 99-110

```python
   99     df = add_recent_form(df, window=config["form_window"])
  100
  101     # 计算进球状态
  102     home_goals_data = df[["home", "home_goals", "away_goals"]].copy()
! 103     home_goals_data.columns = pd.Index(["team", "goals_for", "goals_against"])
  104
  105     away_goals_data = df[["away", "away_goals", "home_goals"]].copy()
! 106     away_goals_data.columns = pd.Index(["team", "goals_for", "goals_against"])
  107
  108     # 合并进球数据
  109     all_goals_data = pd.concat([home_goals_data, away_goals_data])
  110     all_goals_data = all_goals_data.reset_index()
```


---


Lines 136-144

```python
  136         .reset_index()
  137     )
  138
  139     # 为主队添加统计
! 140     df = df.merge(
  141         team_stats, left_on="home", right_on="team", how="left", suffixes=("", "_home")
  142     )
  143     df = df.rename(
  144         columns={
```


---


Lines 148-156

```python
  148     )
  149     df = df.drop("team", axis=1)
  150
  151     # 为客队添加统计
! 152     df = df.merge(
  153         team_stats, left_on="away", right_on="team", how="left", suffixes=("", "_away")
  154     )
  155     df = df.rename(
  156         columns={
```


---


Lines 254-264

```python
  254
  255     # 输入验证和安全检查
  256     def validate_team_name(name: str, field_name: str) -> str:
  257         if not isinstance(name, str):
! 258             raise ValueError(f"{field_name}必须是字符串类型")
  259         if len(name) > 100:  # 防止DoS攻击
! 260             raise ValueError(f"{field_name}长度不能超过100个字符")
  261         if not name.strip():
  262             raise ValueError(f"{field_name}不能为空")
  263         return name.strip()
```


---


Lines 264-278

```python
  264
  265     def validate_odds(value: float, field_name: str) -> float:
  266         # 类型检查
  267         if not isinstance(value, (int, float)):
! 268             raise ValueError(f"{field_name}必须是数字类型,收到:{type(value)}")
  269
  270         # 转换为float
  271         try:
  272             odds_value = float(value)
! 273         except (ValueError, TypeError):
! 274             raise ValueError(f"{field_name}无法转换为数字:{value}")
  275
  276         # 数值有效性检查
  277         import math
```


---


Lines 276-290

```python
  276         # 数值有效性检查
  277         import math
  278
  279         if math.isnan(odds_value):
! 280             raise ValueError(f"{field_name}不能是NaN")
  281         if math.isinf(odds_value):
! 282             raise ValueError(f"{field_name}不能是无穷大")
  283         if odds_value <= 0:
  284             raise ValueError(f"{field_name}必须大于0,收到:{odds_value}")
  285         if odds_value > 1000:  # 合理的上限
! 286             raise ValueError(f"{field_name}过大,最大值1000,收到:{odds_value}")
  287
  288         return odds_value
  289
  290     # 验证输入
```


---


Lines 320-332

```python
  320     if team_stats:
  321         features["home_form"] = team_stats.get("home_form", 1.5)
  322         features["away_form"] = team_stats.get("away_form", 1.5)
  323         features["home_avg_goals_for"] = team_stats.get("home_avg_goals_for", 1.5)
! 324         features["home_avg_goals_against"] = team_stats.get(
  325             "home_avg_goals_against", 1.5
  326         )
  327         features["away_avg_goals_for"] = team_stats.get("away_avg_goals_for", 1.5)
! 328         features["away_avg_goals_against"] = team_stats.get(
  329             "away_avg_goals_against", 1.5
  330         )
  331     else:
  332         # 使用默认值
```


---



## data_pipeline/ingest/csv_adapter&#46;py

Lines 59-67

```python
  59
  60         except pd.errors.EmptyDataError as e:
  61             raise DataSourceError(f"CSV文件为空: {self.file_path}") from e
  62         except pd.errors.ParserError as e:
! 63             raise DataSourceError(
  64                 f"CSV文件解析失败: {self.file_path}, 错误: {e}"
  65             ) from e
  66         except Exception as e:
  67             raise DataSourceError(
```


---


Lines 119-127

```python
  119
  120         except pd.errors.EmptyDataError as e:
  121             raise DataSourceError(f"CSV文件为空: {self.file_path}") from e
  122         except pd.errors.ParserError as e:
! 123             raise DataSourceError(
  124                 f"CSV文件解析失败: {self.file_path}, 错误: {e}"
  125             ) from e
  126         except Exception as e:
  127             raise DataSourceError(
```


---



## data_pipeline/sources/ingest_odds&#46;py

Lines 98-106

```python
   98
   99
  100 def main() -> None:
  101     parser = argparse.ArgumentParser(description="Fetch and ingest odds data.")
! 102     parser.add_argument(
  103         "--start", required=True, help="Start date in YYYY-MM-DD format."
  104     )
  105     parser.add_argument("--end", required=True, help="End date in YYYY-MM-DD format.")
  106     parser.add_argument(
```


---



## models/predictor&#46;py

Lines 86-94

```python
  86             if metrics_file.exists():
  87                 with open(metrics_file, encoding="utf-8") as f:
  88                     metrics = json.load(f)
  89                     if "feature_importance" in metrics:
! 90                         self.feature_columns = list(
  91                             metrics["feature_importance"].keys()
  92                         )
  93
  94             print(f"模型加载成功: {self.model_version}")
```


---


Lines 98-106

```python
   98             import warnings
   99
  100             warnings.warn(f"模型加载失败,使用默认模型: {e}", stacklevel=2)
  101             self.model = _StubModel()
! 102             self.model_version = "stub-default"
  103
  104     def predict_single(
  105         self,
  106         home_team: str,
```


---


Lines 140-150

```python
  140             )
  141         except ValueError as e:
  142             # 重新抛出验证错误,提供更好的错误信息
  143             raise ValueError(f"输入验证失败: {e}") from e
! 144         except Exception as e:
  145             # 捕获其他意外错误
! 146             raise RuntimeError(f"特征生成失败: {e}") from e
  147
  148         # 转换为DataFrame
  149         feature_df = pd.DataFrame([features])
```


---


Lines 157-166

```python
  157
  158         try:
  159             # 预测
  160             proba = self.model.predict_proba(feature_df)[0]
! 161         except Exception as e:
! 162             raise RuntimeError(f"模型预测失败: {e}") from e
  163
  164         # 确定预测结果
  165         prob_home = float(proba[0])
  166         prob_draw = float(proba[1])
```


---


Lines 171-180

```python
  171         if max_prob == prob_home:
  172             predicted_outcome = "home_win"
  173             confidence = prob_home
  174         elif max_prob == prob_draw:
! 175             predicted_outcome = "draw"
! 176             confidence = prob_draw
  177         else:
  178             predicted_outcome = "away_win"
  179             confidence = prob_away
```


---



## models/registry&#46;py

Lines 249-257

```python
  249             metadata_dict = json.load(f)
  250
  251         # 转换日期字符串
  252         if isinstance(metadata_dict["training_date"], str):
! 253             metadata_dict["training_date"] = datetime.fromisoformat(
  254                 metadata_dict["training_date"]
  255             )
  256
  257         return ModelMetadata(**metadata_dict)
```


---



## trainer/fit_xgb&#46;py

Lines 59-67

```python
  59         # 目标变量
  60         df["target"] = df["result"].map({"H": 0, "D": 1, "A": 2})
  61
  62         # 选择特征列
! 63         feature_cols = [
  64             "prob_h",
  65             "prob_d",
  66             "prob_a",
  67             "prob_h_norm",
```


---


Lines 189-197

```python
  189         model = train_xgboost_model(X_train, y_train)
  190
  191         # 5. 评估模型
  192         print("评估模型...")
! 193         _metrics = evaluate_model(model, X_test, y_test)
  194
  195         # 6. 保存模型
  196         # version = save_model_and_metrics(model, metrics)
```


---
