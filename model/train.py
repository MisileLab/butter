import numpy as np
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import MinMaxScaler

# 데이터 전처리를 위한 MinMaxScaler 설정 (입력 및 출력 범위 -100 ~ 100)
scaler = MinMaxScaler(feature_range=(-100, 100))

# 샘플 데이터 생성 (여기선 임의로 생성, 실제 데이터에 맞게 수정 가능)
input_data = np.random.uniform(-100, 100, (1000, 8))  # 1000개의 샘플, 각 샘플 8개의 파라미터
output_data = np.random.uniform(-100, 100, (1000, 8))  # 1000개의 출력 데이터

# 데이터 스케일링
input_scaled = scaler.fit_transform(input_data)
output_scaled = scaler.fit_transform(output_data)

# 모델 구축
model = keras.Sequential([
    keras.layers.Input(shape=(8,)),           # 입력층: 8개의 입력 파라미터
    keras.layers.Dense(64, activation='relu'), # 은닉층 1: 64개의 노드, ReLU 활성화 함수
    keras.layers.Dense(32, activation='relu'), # 은닉층 2: 32개의 노드, ReLU 활성화 함수
    keras.layers.Dense(8)                     # 출력층: 8개의 출력 파라미터
])

# 모델 컴파일
model.compile(optimizer='adam', loss='mse')

# 모델 학습
model.fit(input_scaled, output_scaled, epochs=50, batch_size=32)

# 랜덤 노이즈 추가 함수
def add_random_noise(predictions, noise_factor=0.05):
    noise = np.random.normal(loc=0.0, scale=noise_factor, size=predictions.shape)
    return predictions + noise

# 예측 및 랜덤 노이즈 추가
test_input = np.random.uniform(-100, 100, (1, 8))  # 테스트 입력 데이터
test_input_scaled = scaler.transform(test_input)   # 스케일 조정

# 예측값 도출
predicted_output_scaled = model.predict(test_input_scaled)
predicted_output_noisy = add_random_noise(predicted_output_scaled)  # 노이즈 추가
predicted_output = scaler.inverse_transform(predicted_output_noisy)  # 원래 스케일로 되돌림

print(f"입력값: {test_input}")
print(f"예측 출력값 (랜덤 노이즈 포함): {predicted_output}")
