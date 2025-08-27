# Diff Coverage
## Diff: origin/main...HEAD, staged and unstaged changes

- apps/api/main&#46;py (85.9%): Missing lines 65-70,92-93,154-155
- data_pipeline/features/build&#46;py (11.0%): Missing lines 29-30,33,36,39,42,45,48,51,53,58,69,72-73,76,79-81,84-85,87,92,95,98-99,101-102,105-106,109,118,129,136-137,143,146-147,153,155,160,163-165,168-171,174-177,180,182,187,193-196,201,206,209-212,215-216,218,243,246-248,251-253,256-259,262-263,266-272,275-280,283-285,287
- data_pipeline/features/rolling&#46;py (18.3%): Missing lines 61-62,64,67,70,78,80,105-106,108-109,111,113-114,118-119,125-126,132-133,139-140,146-147,154,156,170-173,175,189,192-194,197-199,202,207,211-213,216-218,221-222,224
- data_pipeline/ingest/base&#46;py (100%)
- data_pipeline/ingest/csv_adapter&#46;py (84.8%): Missing lines 46,63,99,102,117,119,143-144,149-150
- models/predictor&#46;py (18.2%): Missing lines 26-28,30-31,33-34,38-40,43-45,48,50-52,54,63-64,67-68,71-76,78,80,82,84-85,110-111,114,117,120-124,127,129,146-147,149-152,160-161,163,173,177-178,180,187-189,191,196,202,204,209-210,212-215,217-218
- trainer/fit_xgb&#46;py (18.9%): Missing lines 25-26,28-29,31,36-40,43,46-48,51-54,57,60-61,63,70-71,82-83,85,93-94,97-98,101,105,114,122-123,126-127,130-132,135-137,139-142,144,149,151,153-156,159-161,164-165,167-168,171,176-177,180-181,184,186-187,189-191

## Summary

- **Total**: 500 lines
- **Missing**: 311 lines
- **Coverage**: 37%



## apps/api/main&#46;py

Lines 61-74

```python
  61 @app.on_event("startup")
  62 async def startup_event():
  63     """应用启动时初始化预测器"""
  64     global predictor
! 65     try:
! 66         predictor = create_predictor()
! 67         if predictor.model is None:
! 68             print("警告: 未找到模型文件,API将使用默认预测")
! 69     except Exception as e:
! 70         print(f"预测器初始化失败: {e}")
  71
  72
  73 @app.get("/health", response_model=HealthResponse)
  74 async def health_check():
```


---


Lines 88-97

```python
  88     model_info = {}
  89     model_version = "unknown"
  90
  91     if predictor and predictor.model is not None:
! 92         model_info = predictor.get_model_info()
! 93         model_version = predictor.model_version or "unknown"
  94
  95     return VersionResponse(api_version="1.0.0", model_version=model_version, model_info=model_info)
  96
```


---


Lines 150-159

```python
  150             )
  151
  152         return results
  153
! 154     except Exception as e:
! 155         raise HTTPException(status_code=500, detail=f"预测失败: {e!s}") from None
  156
  157
  158 @app.get("/")
  159 async def root():
```


---



## data_pipeline/features/build&#46;py

Lines 25-62

```python
  25
  26     Returns:
  27         pd.DataFrame: 特征数据框
  28     """
! 29     if feature_config is None:
! 30         feature_config = get_default_feature_config()
  31
  32     # 确保数据按日期排序
! 33     matches_df = matches_df.sort_values("date").reset_index(drop=True)
  34
  35     # 合并赔率数据
! 36     df = matches_df.merge(odds_df, left_on="id", right_on="match_id", how="left")
  37
  38     # 添加基础特征
! 39     df = add_basic_features(df)
  40
  41     # 添加状态特征
! 42     df = add_form_features(df, feature_config)
  43
  44     # 添加赔率特征
! 45     df = add_odds_features(df)
  46
  47     # 添加历史对战特征
! 48     df = add_head_to_head_features(df, feature_config)
  49
  50     # 清理和标准化
! 51     df = clean_features(df)
  52
! 53     return df
  54
  55
  56 def get_default_feature_config() -> dict[str, Any]:
  57     """获取默认特征配置"""
! 58     return {
  59         "form_window": 5,
  60         "goal_window": 5,
  61         "h2h_window": 10,
  62         "min_matches": 3,
```


---


Lines 65-113

```python
   65
   66
   67 def add_basic_features(df: pd.DataFrame) -> pd.DataFrame:
   68     """添加基础特征"""
!  69     df = df.copy()
   70
   71     # 主客场标识
!  72     df["is_home"] = 1
!  73     df["is_away"] = 0
   74
   75     # 比赛结果编码
!  76     df["target"] = df["result"].map({"H": 0, "D": 1, "A": 2})
   77
   78     # 进球相关特征
!  79     df["total_goals"] = df["home_goals"] + df["away_goals"]
!  80     df["goal_difference"] = df["home_goals"] - df["away_goals"]
!  81     df["both_teams_scored"] = ((df["home_goals"] > 0) & (df["away_goals"] > 0)).astype(int)
   82
   83     # 比赛强度特征
!  84     df["high_scoring"] = (df["total_goals"] > 2.5).astype(int)
!  85     df["low_scoring"] = (df["total_goals"] < 1.5).astype(int)
   86
!  87     return df
   88
   89
   90 def add_form_features(df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
   91     """添加状态特征"""
!  92     df = df.copy()
   93
   94     # 计算近期状态
!  95     df = add_recent_form(df, window=config["form_window"])
   96
   97     # 计算进球状态
!  98     home_goals_data = df[["home", "home_goals", "away_goals"]].copy()
!  99     home_goals_data.columns = ["team", "goals_for", "goals_against"]
  100
! 101     away_goals_data = df[["away", "away_goals", "home_goals"]].copy()
! 102     away_goals_data.columns = ["team", "goals_for", "goals_against"]
  103
  104     # 合并进球数据
! 105     all_goals_data = pd.concat([home_goals_data, away_goals_data])
! 106     all_goals_data = all_goals_data.reset_index()
  107
  108     # 计算滚动进球统计
! 109     all_goals_data = add_rolling_stats(
  110         all_goals_data,
  111         "team",
  112         "goals_for",
  113         window=config["goal_window"],
```


---


Lines 114-122

```python
  114         stats=["mean"],
  115         prefix="avg_",
  116     )
  117
! 118     all_goals_data = add_rolling_stats(
  119         all_goals_data,
  120         "team",
  121         "goals_against",
  122         window=config["goal_window"],
```


---


Lines 125-133

```python
  125     )
  126
  127     # 将进球统计合并回原数据
  128     # 这里简化处理,实际应该基于时间窗口
! 129     team_stats = (
  130         all_goals_data.groupby("team")
  131         .agg({"avg_goals_for_mean_5": "last", "avg_goals_against_mean_5": "last"})
  132         .reset_index()
  133     )
```


---


Lines 132-141

```python
  132         .reset_index()
  133     )
  134
  135     # 为主队添加统计
! 136     df = df.merge(team_stats, left_on="home", right_on="team", how="left", suffixes=("", "_home"))
! 137     df = df.rename(
  138         columns={
  139             "avg_goals_for_mean_5": "home_avg_goals_for",
  140             "avg_goals_against_mean_5": "home_avg_goals_against",
  141         }
```


---


Lines 139-151

```python
  139             "avg_goals_for_mean_5": "home_avg_goals_for",
  140             "avg_goals_against_mean_5": "home_avg_goals_against",
  141         }
  142     )
! 143     df = df.drop("team", axis=1)
  144
  145     # 为客队添加统计
! 146     df = df.merge(team_stats, left_on="away", right_on="team", how="left", suffixes=("", "_away"))
! 147     df = df.rename(
  148         columns={
  149             "avg_goals_for_mean_5": "away_avg_goals_for",
  150             "avg_goals_against_mean_5": "away_avg_goals_against",
  151         }
```


---


Lines 149-191

```python
  149             "avg_goals_for_mean_5": "away_avg_goals_for",
  150             "avg_goals_against_mean_5": "away_avg_goals_against",
  151         }
  152     )
! 153     df = df.drop("team", axis=1)
  154
! 155     return df
  156
  157
  158 def add_odds_features(df: pd.DataFrame) -> pd.DataFrame:
  159     """添加赔率特征"""
! 160     df = df.copy()
  161
  162     # 隐含概率
! 163     df["prob_h"] = 1 / df["h"]
! 164     df["prob_d"] = 1 / df["d"]
! 165     df["prob_a"] = 1 / df["a"]
  166
  167     # 标准化概率(去除赔率商利润)
! 168     total_prob = df["prob_h"] + df["prob_d"] + df["prob_a"]
! 169     df["prob_h_norm"] = df["prob_h"] / total_prob
! 170     df["prob_d_norm"] = df["prob_d"] / total_prob
! 171     df["prob_a_norm"] = df["prob_a"] / total_prob
  172
  173     # 赔率差异特征
! 174     df["odds_spread"] = df["h"].max() - df["h"].min()  # 简化版本
! 175     df["favorite"] = np.where(df["h"] < df["a"], "home", "away")
! 176     df["favorite_odds"] = np.minimum(df["h"], df["a"])
! 177     df["underdog_odds"] = np.maximum(df["h"], df["a"])
  178
  179     # 市场信心度
! 180     df["market_confidence"] = 1 / df["favorite_odds"]
  181
! 182     return df
  183
  184
  185 def add_head_to_head_features(df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
  186     """添加历史对战特征"""
! 187     df = df.copy()
  188
  189     # 简化版本:计算基础对战统计
  190     # 实际实现需要基于历史数据的时间窗口
```


---


Lines 189-222

```python
  189     # 简化版本:计算基础对战统计
  190     # 实际实现需要基于历史数据的时间窗口
  191
  192     # 为每场比赛添加对战记录特征
! 193     df["h2h_home_wins"] = 0  # 占位符
! 194     df["h2h_draws"] = 0  # 占位符
! 195     df["h2h_away_wins"] = 0  # 占位符
! 196     df["h2h_total_matches"] = 0  # 占位符
  197
  198     # 如果有足够的历史数据,这里应该实现真实的对战统计
  199     # 由于这是MVP版本,先用占位符
  200
! 201     return df
  202
  203
  204 def clean_features(df: pd.DataFrame) -> pd.DataFrame:
  205     """清理和标准化特征"""
! 206     df = df.copy()
  207
  208     # 填充缺失值
! 209     numeric_columns = df.select_dtypes(include=[np.number]).columns
! 210     for col in numeric_columns:
! 211         if col not in ["id", "home", "away", "target"]:
! 212             df[col] = df[col].fillna(df[col].mean())
  213
  214     # 移除不需要的列
! 215     columns_to_drop = ["date", "result", "provider", "match_id"]
! 216     df = df.drop([col for col in columns_to_drop if col in df.columns], axis=1)
  217
! 218     return df
  219
  220
  221 def create_feature_vector(
  222     home_team: str,
```


---


Lines 239-288

```python
  239
  240     Returns:
  241         Dict[str, float]: 特征字典
  242     """
! 243     features = {}
  244
  245     # 基础赔率特征
! 246     features["h"] = odds_h
! 247     features["d"] = odds_d
! 248     features["a"] = odds_a
  249
  250     # 隐含概率
! 251     features["prob_h"] = 1 / odds_h
! 252     features["prob_d"] = 1 / odds_d
! 253     features["prob_a"] = 1 / odds_a
  254
  255     # 标准化概率
! 256     total_prob = features["prob_h"] + features["prob_d"] + features["prob_a"]
! 257     features["prob_h_norm"] = features["prob_h"] / total_prob
! 258     features["prob_d_norm"] = features["prob_d"] / total_prob
! 259     features["prob_a_norm"] = features["prob_a"] / total_prob
  260
  261     # 主客场标识
! 262     features["is_home"] = 1
! 263     features["is_away"] = 0
  264
  265     # 如果有球队统计数据,添加相关特征
! 266     if team_stats:
! 267         features["home_form"] = team_stats.get("home_form", 1.5)
! 268         features["away_form"] = team_stats.get("away_form", 1.5)
! 269         features["home_avg_goals_for"] = team_stats.get("home_avg_goals_for", 1.5)
! 270         features["home_avg_goals_against"] = team_stats.get("home_avg_goals_against", 1.5)
! 271         features["away_avg_goals_for"] = team_stats.get("away_avg_goals_for", 1.5)
! 272         features["away_avg_goals_against"] = team_stats.get("away_avg_goals_against", 1.5)
  273     else:
  274         # 使用默认值
! 275         features["home_form"] = 1.5
! 276         features["away_form"] = 1.5
! 277         features["home_avg_goals_for"] = 1.5
! 278         features["home_avg_goals_against"] = 1.5
! 279         features["away_avg_goals_for"] = 1.5
! 280         features["away_avg_goals_against"] = 1.5
  281
  282     # 市场相关特征
! 283     features["favorite_odds"] = min(odds_h, odds_a)
! 284     features["underdog_odds"] = max(odds_h, odds_a)
! 285     features["market_confidence"] = 1 / features["favorite_odds"]
  286
! 287     return features
```


---



## data_pipeline/features/rolling&#46;py

Lines 57-74

```python
  57
  58     Returns:
  59         pd.DataFrame: 添加了'goal_diff'列的数据框
  60     """
! 61     if window <= 0:
! 62         raise ValueError("滚动窗口大小必须大于0")
  63
! 64     df = df.copy()
  65
  66     # 计算净胜球
! 67     df["temp_goal_diff"] = df[goals_for_col] - df[goals_against_col]
  68
  69     # 按球队分组计算滚动平均净胜球
! 70     df["goal_diff"] = (
  71         df.groupby(team_col)["temp_goal_diff"]
  72         .rolling(window=window, min_periods=1)
  73         .mean()
  74         .reset_index(level=0, drop=True)
```


---


Lines 74-84

```python
  74         .reset_index(level=0, drop=True)
  75     )
  76
  77     # 删除临时列
! 78     df = df.drop("temp_goal_diff", axis=1)
  79
! 80     return df
  81
  82
  83 def add_rolling_stats(
  84     df: pd.DataFrame,
```


---


Lines 101-123

```python
  101
  102     Returns:
  103         pd.DataFrame: 添加了滚动统计列的数据框
  104     """
! 105     if stats is None:
! 106         stats = ["mean", "std"]
  107
! 108     if window <= 0:
! 109         raise ValueError("滚动窗口大小必须大于0")
  110
! 111     df = df.copy()
  112
! 113     for stat in stats:
! 114         col_name = (
  115             f"{prefix}{value_col}_{stat}_{window}" if prefix else f"{value_col}_{stat}_{window}"
  116         )
  117
! 118         if stat == "mean":
! 119             df[col_name] = (
  120                 df.groupby(team_col)[value_col]
  121                 .rolling(window=window, min_periods=1)
  122                 .mean()
  123                 .reset_index(level=0, drop=True)
```


---


Lines 121-130

```python
  121                 .rolling(window=window, min_periods=1)
  122                 .mean()
  123                 .reset_index(level=0, drop=True)
  124             )
! 125         elif stat == "std":
! 126             df[col_name] = (
  127                 df.groupby(team_col)[value_col]
  128                 .rolling(window=window, min_periods=2)
  129                 .std()
  130                 .reset_index(level=0, drop=True)
```


---


Lines 128-137

```python
  128                 .rolling(window=window, min_periods=2)
  129                 .std()
  130                 .reset_index(level=0, drop=True)
  131             )
! 132         elif stat == "sum":
! 133             df[col_name] = (
  134                 df.groupby(team_col)[value_col]
  135                 .rolling(window=window, min_periods=1)
  136                 .sum()
  137                 .reset_index(level=0, drop=True)
```


---


Lines 135-144

```python
  135                 .rolling(window=window, min_periods=1)
  136                 .sum()
  137                 .reset_index(level=0, drop=True)
  138             )
! 139         elif stat == "max":
! 140             df[col_name] = (
  141                 df.groupby(team_col)[value_col]
  142                 .rolling(window=window, min_periods=1)
  143                 .max()
  144                 .reset_index(level=0, drop=True)
```


---


Lines 142-151

```python
  142                 .rolling(window=window, min_periods=1)
  143                 .max()
  144                 .reset_index(level=0, drop=True)
  145             )
! 146         elif stat == "min":
! 147             df[col_name] = (
  148                 df.groupby(team_col)[value_col]
  149                 .rolling(window=window, min_periods=1)
  150                 .min()
  151                 .reset_index(level=0, drop=True)
```


---


Lines 150-160

```python
  150                 .min()
  151                 .reset_index(level=0, drop=True)
  152             )
  153         else:
! 154             raise ValueError(f"不支持的统计函数: {stat}")
  155
! 156     return df
  157
  158
  159 def calculate_points(result: str, is_home: bool) -> int:
  160     """
```


---


Lines 166-179

```python
  166
  167     Returns:
  168         int: 积分 (3胜/1平/0负)
  169     """
! 170     if result == "D":  # 平局
! 171         return 1
! 172     elif (result == "H" and is_home) or (result == "A" and not is_home):
! 173         return 3  # 胜利
  174     else:
! 175         return 0  # 失败
  176
  177
  178 def add_recent_form(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
  179     """
```


---


Lines 185-225

```python
  185
  186     Returns:
  187         pd.DataFrame: 添加了 'home_form', 'away_form' 列的数据框
  188     """
! 189     df = df.copy()
  190
  191     # 创建主队数据
! 192     home_data = df[["home", "result"]].copy()
! 193     home_data["team"] = home_data["home"]
! 194     home_data["points"] = home_data["result"].apply(lambda x: calculate_points(x, is_home=True))
  195
  196     # 创建客队数据
! 197     away_data = df[["away", "result"]].copy()
! 198     away_data["team"] = away_data["away"]
! 199     away_data["points"] = away_data["result"].apply(lambda x: calculate_points(x, is_home=False))
  200
  201     # 合并所有球队数据
! 202     all_team_data = pd.concat(
  203         [home_data[["team", "points"]], away_data[["team", "points"]]]
  204     ).reset_index()
  205
  206     # 计算滚动状态
! 207     all_team_data = add_form(all_team_data, "team", "points", window)
  208
  209     # 将状态合并回原数据
  210     # 为主队添加状态
! 211     home_form_data = all_team_data[all_team_data["team"].isin(df["home"])]
! 212     home_form_map = dict(zip(home_form_data.index, home_form_data["form"], strict=False))
! 213     df["home_form"] = df.index.map(home_form_map)
  214
  215     # 为客队添加状态
! 216     away_form_data = all_team_data[all_team_data["team"].isin(df["away"])]
! 217     away_form_map = dict(zip(away_form_data.index, away_form_data["form"], strict=False))
! 218     df["away_form"] = df.index.map(away_form_map)
  219
  220     # 填充缺失值
! 221     df["home_form"] = df["home_form"].fillna(1.5)  # 默认状态
! 222     df["away_form"] = df["away_form"].fillna(1.5)  # 默认状态
  223
! 224     return df
```


---



## data_pipeline/ingest/csv_adapter&#46;py

Lines 42-50

```python
  42
  43             df = pd.read_csv(self.file_path)
  44
  45             if df.empty:
! 46                 raise DataSourceError(f"CSV文件为空: {self.file_path}")
  47
  48             if not self.validate(df):
  49                 raise DataSourceError(f"CSV文件格式不正确: {self.file_path}")
```


---


Lines 59-67

```python
  59
  60         except pd.errors.EmptyDataError as e:
  61             raise DataSourceError(f"CSV文件为空: {self.file_path}") from e
  62         except pd.errors.ParserError as e:
! 63             raise DataSourceError(f"CSV文件解析失败: {self.file_path}, 错误: {e}") from e
  64         except Exception as e:
  65             raise DataSourceError(f"读取CSV文件失败: {self.file_path}, 错误: {e}") from e
  66
```


---


Lines 95-106

```python
   95
   96             df = pd.read_csv(self.file_path)
   97
   98             if df.empty:
!  99                 raise DataSourceError(f"CSV文件为空: {self.file_path}")
  100
  101             if not self.validate(df):
! 102                 raise DataSourceError(f"CSV文件格式不正确: {self.file_path}")
  103
  104             # 转换数据类型
  105             df["match_id"] = df["match_id"].astype(int)
  106             df["h"] = df["h"].astype(float)
```


---


Lines 113-123

```python
  113
  114             return df
  115
  116         except pd.errors.EmptyDataError as e:
! 117             raise DataSourceError(f"CSV文件为空: {self.file_path}") from e
  118         except pd.errors.ParserError as e:
! 119             raise DataSourceError(f"CSV文件解析失败: {self.file_path}, 错误: {e}") from e
  120         except Exception as e:
  121             raise DataSourceError(f"读取CSV文件失败: {self.file_path}, 错误: {e}") from e
  122
```


---


Lines 139-151

```python
  139
  140
  141 def create_sample_match_source() -> CSVMatchDataSource:
  142     """创建样例比赛数据源"""
! 143     file_path = get_sample_data_path("matches.csv")
! 144     return CSVMatchDataSource(file_path)
  145
  146
  147 def create_sample_odds_source() -> CSVOddsDataSource:
  148     """创建样例赔率数据源"""
! 149     file_path = get_sample_data_path("odds.csv")
! 150     return CSVOddsDataSource(file_path)
```


---



## models/predictor&#46;py

Lines 22-58

```python
  22
  23         Args:
  24             model_path: 模型文件路径,如果为None则加载最新模型
  25         """
! 26         self.model = None
! 27         self.model_version = None
! 28         self.feature_columns = None
  29
! 30         if model_path is None:
! 31             model_path = self._find_latest_model()
  32
! 33         if model_path:
! 34             self.load_model(model_path)
  35
  36     def _find_latest_model(self) -> str | None:
  37         """查找最新的模型文件"""
! 38         models_dir = Path("models")
! 39         if not models_dir.exists():
! 40             return None
  41
  42         # 查找所有模型目录
! 43         model_dirs = [d for d in models_dir.iterdir() if d.is_dir()]
! 44         if not model_dirs:
! 45             return None
  46
  47         # 按创建时间排序,选择最新的
! 48         latest_dir = max(model_dirs, key=lambda x: x.stat().st_ctime)
  49
! 50         model_file = latest_dir / "model.pkl"
! 51         if model_file.exists():
! 52             return str(model_file)
  53
! 54         return None
  55
  56     def load_model(self, model_path: str):
  57         """
  58         加载模型
```


---


Lines 59-89

```python
  59
  60         Args:
  61             model_path: 模型文件路径
  62         """
! 63         try:
! 64             self.model = _safe_load_or_stub(model_path)
  65
  66             # 获取模型版本信息
! 67             model_dir = Path(model_path).parent
! 68             self.model_version = model_dir.name
  69
  70             # 尝试加载特征列信息
! 71             metrics_file = model_dir / "metrics.json"
! 72             if metrics_file.exists():
! 73                 with open(metrics_file, encoding="utf-8") as f:
! 74                     metrics = json.load(f)
! 75                     if "feature_importance" in metrics:
! 76                         self.feature_columns = list(metrics["feature_importance"].keys())
  77
! 78             print(f"模型加载成功: {self.model_version}")
  79
! 80         except Exception as e:
  81             # 如果加载失败,使用stub模型
! 82             import warnings
  83
! 84             warnings.warn(f"模型加载失败,使用默认模型: {e}", stacklevel=2)
! 85             self.model = _StubModel()
  86
  87     def predict_single(
  88         self,
  89         home_team: str,
```


---


Lines 106-133

```python
  106
  107         Returns:
  108             Dict[str, float]: 预测概率 {'home_win': 0.4, 'draw': 0.3, 'away_win': 0.3}
  109         """
! 110         if self.model is None:
! 111             raise RuntimeError("模型未加载")
  112
  113         # 创建特征向量
! 114         features = create_feature_vector(home_team, away_team, odds_h, odds_d, odds_a, team_stats)
  115
  116         # 转换为DataFrame
! 117         feature_df = pd.DataFrame([features])
  118
  119         # 如果有特征列信息,确保列顺序一致
! 120         if self.feature_columns:
! 121             missing_cols = set(self.feature_columns) - set(feature_df.columns)
! 122             for col in missing_cols:
! 123                 feature_df[col] = 0.0  # 填充缺失特征
! 124             feature_df = feature_df[self.feature_columns]
  125
  126         # 预测
! 127         proba = self.model.predict_proba(feature_df)[0]
  128
! 129         return {
  130             "home_win": float(proba[0]),
  131             "draw": float(proba[1]),
  132             "away_win": float(proba[2]),
  133             "model_version": self.model_version,
```


---


Lines 142-156

```python
  142
  143         Returns:
  144             List[Dict[str, float]]: 预测结果列表
  145         """
! 146         if self.model is None:
! 147             raise RuntimeError("模型未加载")
  148
! 149         results = []
! 150         for match in matches:
! 151             try:
! 152                 result = self.predict_single(
  153                     home_team=match.get("home", ""),
  154                     away_team=match.get("away", ""),
  155                     odds_h=match.get("odds_h", match.get("h", 2.0)),
  156                     odds_d=match.get("odds_d", match.get("d", 3.0)),
```


---


Lines 156-167

```python
  156                     odds_d=match.get("odds_d", match.get("d", 3.0)),
  157                     odds_a=match.get("odds_a", match.get("a", 3.0)),
  158                     team_stats=match.get("team_stats"),
  159                 )
! 160                 results.append(result)
! 161             except Exception as e:
  162                 # 返回默认预测(平均分布)
! 163                 results.append(
  164                     {
  165                         "home_win": 0.33,
  166                         "draw": 0.34,
  167                         "away_win": 0.33,
```


---


Lines 169-184

```python
  169                         "error": str(e),
  170                     }
  171                 )
  172
! 173         return results
  174
  175     def get_model_info(self) -> dict[str, Any]:
  176         """获取模型信息"""
! 177         if self.model is None:
! 178             return {"status": "no_model_loaded"}
  179
! 180         info = {
  181             "model_version": self.model_version,
  182             "model_type": type(self.model).__name__,
  183             "is_loaded": True,
  184         }
```


---


Lines 183-200

```python
  183             "is_loaded": True,
  184         }
  185
  186         # 如果有特征列信息
! 187         if self.feature_columns:
! 188             info["n_features"] = len(self.feature_columns)
! 189             info["feature_columns"] = self.feature_columns
  190
! 191         return info
  192
  193
  194 def create_predictor(model_path: str | None = None) -> Predictor:
  195     """创建预测器实例"""
! 196     return Predictor(model_path)
  197
  198
  199 # --- Fallback: stub when no model present ---
  200 class _StubModel:
```


---


Lines 198-219

```python
  198
  199 # --- Fallback: stub when no model present ---
  200 class _StubModel:
  201     def predict_proba(self, X):
! 202         import numpy as np
  203
! 204         return np.array([[0.34, 0.33, 0.33] for _ in range(len(X))])
  205
  206
  207 def _safe_load_or_stub(path: str):
  208     """安全加载模型,失败时返回stub"""
! 209     try:
! 210         import pickle
  211
! 212         with open(path, "rb") as f:
! 213             return pickle.load(f)
! 214     except Exception:
! 215         import warnings
  216
! 217         warnings.warn("Predictor: model missing, using stub", stacklevel=2)
! 218         return _StubModel()
```


---



## trainer/fit_xgb&#46;py

Lines 21-67

```python
  21
  22 def load_training_data() -> tuple[pd.DataFrame, pd.DataFrame]:
  23     """加载训练数据"""
  24     # 从样例数据加载
! 25     matches_source = create_sample_match_source()
! 26     odds_source = create_sample_odds_source()
  27
! 28     matches_df = matches_source.fetch()
! 29     odds_df = odds_source.fetch()
  30
! 31     return matches_df, odds_df
  32
  33
  34 def prepare_features(matches_df: pd.DataFrame, odds_df: pd.DataFrame) -> pd.DataFrame:
  35     """准备特征数据"""
! 36     try:
! 37         features_df = build_match_features(matches_df, odds_df)
! 38         return features_df
! 39     except Exception as e:
! 40         print(f"特征构建失败,使用简化版本: {e}")
  41
  42         # 简化版本的特征构建
! 43         df = matches_df.merge(odds_df, left_on="id", right_on="match_id", how="left")
  44
  45         # 基础特征
! 46         df["prob_h"] = 1 / df["h"]
! 47         df["prob_d"] = 1 / df["d"]
! 48         df["prob_a"] = 1 / df["a"]
  49
  50         # 标准化概率
! 51         total_prob = df["prob_h"] + df["prob_d"] + df["prob_a"]
! 52         df["prob_h_norm"] = df["prob_h"] / total_prob
! 53         df["prob_d_norm"] = df["prob_d"] / total_prob
! 54         df["prob_a_norm"] = df["prob_a"] / total_prob
  55
  56         # 目标变量
! 57         df["target"] = df["result"].map({"H": 0, "D": 1, "A": 2})
  58
  59         # 选择特征列
! 60         feature_cols = ["prob_h", "prob_d", "prob_a", "prob_h_norm", "prob_d_norm", "prob_a_norm"]
! 61         df = df[[*feature_cols, "target"]].dropna()
  62
! 63         return df
  64
  65
  66 def train_xgboost_model(
  67     X: pd.DataFrame, y: pd.Series, model_config: dict[str, Any] | None = None
```


---


Lines 66-75

```python
  66 def train_xgboost_model(
  67     X: pd.DataFrame, y: pd.Series, model_config: dict[str, Any] | None = None
  68 ) -> xgb.XGBClassifier:
  69     """训练XGBoost模型"""
! 70     if model_config is None:
! 71         model_config = {
  72             "n_estimators": 100,
  73             "max_depth": 6,
  74             "learning_rate": 0.1,
  75             "subsample": 0.8,
```


---


Lines 78-89

```python
  78             "objective": "multi:softprob",
  79             "num_class": 3,
  80         }
  81
! 82     model = xgb.XGBClassifier(**model_config)
! 83     model.fit(X, y)
  84
! 85     return model
  86
  87
  88 def evaluate_model(
  89     model: xgb.XGBClassifier, X_test: pd.DataFrame, y_test: pd.Series
```


---


Lines 89-109

```python
   89     model: xgb.XGBClassifier, X_test: pd.DataFrame, y_test: pd.Series
   90 ) -> dict[str, Any]:
   91     """评估模型性能"""
   92     # 预测
!  93     y_pred = model.predict(X_test)
!  94     y_pred_proba = model.predict_proba(X_test)
   95
   96     # 计算指标
!  97     accuracy = accuracy_score(y_test, y_pred)
!  98     logloss = log_loss(y_test, y_pred_proba)
   99
  100     # 分类报告
! 101     class_report = classification_report(
  102         y_test, y_pred, target_names=["Home", "Draw", "Away"], output_dict=True
  103     )
  104
! 105     metrics = {
  106         "accuracy": float(accuracy),
  107         "log_loss": float(logloss),
  108         "classification_report": class_report,
  109         "feature_importance": dict(zip(X_test.columns, model.feature_importances_, strict=False)),
```


---


Lines 110-118

```python
  110         "n_samples_train": len(X_test),
  111         "n_features": len(X_test.columns),
  112     }
  113
! 114     return metrics
  115
  116
  117 def save_model_and_metrics(
  118     model: xgb.XGBClassifier, metrics: dict[str, Any], model_dir: str = "models"
```


---


Lines 118-195

```python
  118     model: xgb.XGBClassifier, metrics: dict[str, Any], model_dir: str = "models"
  119 ) -> str:
  120     """保存模型和指标"""
  121     # 创建带时间戳的模型版本
! 122     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
! 123     version = f"xgb_{timestamp}"
  124
  125     # 创建模型目录
! 126     model_path = Path(model_dir) / version
! 127     model_path.mkdir(parents=True, exist_ok=True)
  128
  129     # 保存模型
! 130     model_file = model_path / "model.pkl"
! 131     with open(model_file, "wb") as f:
! 132         pickle.dump(model, f)
  133
  134     # 保存指标
! 135     metrics_file = model_path / "metrics.json"
! 136     with open(metrics_file, "w", encoding="utf-8") as f:
! 137         json.dump(metrics, f, ensure_ascii=False, indent=2)
  138
! 139     print(f"模型已保存至: {model_path}")
! 140     print(f"模型版本: {version}")
! 141     print(f"准确率: {metrics['accuracy']:.4f}")
! 142     print(f"对数损失: {metrics['log_loss']:.4f}")
  143
! 144     return version
  145
  146
  147 def main():
  148     """主训练流程"""
! 149     print("开始训练XGBoost模型...")
  150
! 151     try:
  152         # 1. 加载数据
! 153         print("加载训练数据...")
! 154         matches_df, odds_df = load_training_data()
! 155         print(f"比赛数据: {len(matches_df)} 条")
! 156         print(f"赔率数据: {len(odds_df)} 条")
  157
  158         # 2. 准备特征
! 159         print("构建特征...")
! 160         features_df = prepare_features(matches_df, odds_df)
! 161         print(f"特征数据: {features_df.shape}")
  162
  163         # 分离特征和目标
! 164         X = features_df.drop("target", axis=1)
! 165         y = features_df["target"]
  166
! 167         print(f"特征列: {list(X.columns)}")
! 168         print(f"目标分布: \n{y.value_counts()}")
  169
  170         # 3. 划分训练测试集
! 171         X_train, X_test, y_train, y_test = train_test_split(
  172             X, y, test_size=0.2, random_state=42, stratify=y
  173         )
  174
  175         # 4. 训练模型
! 176         print("训练模型...")
! 177         model = train_xgboost_model(X_train, y_train)
  178
  179         # 5. 评估模型
! 180         print("评估模型...")
! 181         metrics = evaluate_model(model, X_test, y_test)
  182
  183         # 6. 保存模型
! 184         version = save_model_and_metrics(model, metrics)
  185
! 186         print("训练完成!")
! 187         return version
  188
! 189     except Exception as e:
! 190         print(f"训练失败: {e}")
! 191         raise
  192
  193
  194 if __name__ == "__main__":
  195     main()
```


---
