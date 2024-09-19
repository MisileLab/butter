import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
import numpy as np

# 모델 생성
model = Sequential([
    Dense(64, input_dim=11, activation='relu'),  # 첫 번째 레이어
    Dense(64, activation='relu'),  # 두 번째 레이어
    Dense(11)  # 출력 레이어
])

# 모델 컴파일
model.compile(optimizer='adam', loss='mean_squared_error')

# 데이터 생성 (예시용)
# 입력 데이터 (예: 100개의 샘플)
X_train = np.random.uniform(-90, 90, (100, 11))

# 출력 데이터 (예: 100개의 샘플)
y_train = np.random.uniform(-90, 90, (100, 11))

# 모델 훈련
model.fit(X_train, y_train, epochs=50, batch_size=10, verbose=1)

# 모델 평가
loss = model.evaluate(X_train, y_train)
print(f"Loss: {loss}")

# 예측
predictions = model.predict(X_train)
print(predictions)
