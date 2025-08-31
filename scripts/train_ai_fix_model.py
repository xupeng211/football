# AI-Fix-Enhancement: Placeholder script for future AI bug-fix model training

import pickle
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

# --- 配置 --- #
# 定义项目根目录, 以便脚本可以在任何位置运行
PROJECT_ROOT = Path(__file__).parent.parent
BUG_FIXES_DIR = PROJECT_ROOT / "data" / "bug_fixes"
FEEDBACK_DIR = PROJECT_ROOT / "data" / "feedback"
MODEL_ARTIFACTS_DIR = PROJECT_ROOT / "models" / "artifacts"


# --- 核心功能 --- #
def load_data():
    """加载bug修复和反馈数据(模拟)."""
    print("🔍 加载数据...")
    # 在真实场景中, 这里会解析JSON或CSV文件
    # 这里我们使用模拟的DataFrame
    data = {
        "bug_description": [
            "division by zero in calculate_ratio",
            "null pointer on negative id",
            "api timeout on large payload",
            "incorrect currency conversion",
        ],
        "code_patch": [
            "if b == 0: return 0",
            "if id < 0: return null",
            "increase client timeout to 60s",
            "rate = get_rate_from_db()",
        ],
        "is_correct_fix": [1, 1, 0, 1],  # 1 = good fix, 0 = bad fix
    }
    df = pd.DataFrame(data)
    print(f"✅ 加载了 {len(df)} 条数据记录.")
    return df


def preprocess_data(df):
    """数据预处理和特征工程."""
    print("⚙️  预处理数据...")
    # 将bug描述和代码补丁合并为一个文本特征
    df["text_features"] = df["bug_description"] + " " + df["code_patch"]
    print(f"正确修复标签分布: {df['is_correct_fix'].value_counts().to_dict()}")
    return df


def train_model(df):
    """训练AI修复分类模型."""
    print("🤖 训练模型...")
    # 准备特征和标签
    X = df["text_features"]
    y = df["is_correct_fix"]

    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42
    )

    # TF-IDF向量化
    vectorizer = TfidfVectorizer()
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # 训练逻辑回归模型
    model = LogisticRegression()
    model.fit(X_train_vec, y_train)

    # 评估模型
    y_pred = model.predict(X_test_vec)
    acc = accuracy_score(y_test, y_pred)
    print(f"📈 模型评估准确率: {acc:.2f}")

    return model, vectorizer, acc


def save_model(model, vectorizer):
    """将模型和向量化器保存到文件."""
    print("💾 保存模型...")
    MODEL_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_ARTIFACTS_DIR / "ai_fix_classifier.pkl"
    vectorizer_path = MODEL_ARTIFACTS_DIR / "ai_fix_vectorizer.pkl"

    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    with open(vectorizer_path, "wb") as f:
        pickle.dump(vectorizer, f)

    print("✅ 模型已成功保存.")


# --- 主函数 --- #
def main():
    """执行完整的训练流程."""
    print("🚀 --- 开始AI修复模型训练流程 --- 🚀")
    df = load_data()
    df = preprocess_data(df)
    model, vectorizer, accuracy = train_model(df)

    if accuracy > 0.7:  # 只有当模型达到一定标准时才保存
        save_model(model, vectorizer)
    else:
        print("模型的准确率过低, 不予保存.")

    print("🏁 --- 训练流程结束 --- 🏁")


if __name__ == "__main__":
    main()
