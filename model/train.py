from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
import numpy as np

from os import listdir
from json import load

model = Sequential([
  Dense(64, input_dim=9, activation='relu'),
  Dense(64, activation='relu'),
  Dense(64, activation='relu'),
  Dense(9)
])

model.compile(optimizer='adam', loss='mean_squared_error')

datas = [
  load(open(f'/content/drive/MyDrive/data/{i}'))['data'] for i in listdir('/content/drive/MyDrive/data')
]
params = []
results = []

for data in datas:
  for i in range(1, len(data)):
    params.append(data[i-1])
    results.append(data[i])

params, results = np.array(params), np.array(results)

model.fit(params, results, epochs=10, batch_size=10, verbose=1)

loss = model.evaluate(params, results)
print(f"Loss: {loss}")

predictions = model.predict(np.zeros((1, 9)))
print(predictions)

model.save('/content/model.keras')
