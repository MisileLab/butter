from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, InputLayer, Flatten
import numpy as np

from os import listdir
from json import load

model = Sequential([
  InputLayer(input_shape=(9, 2)),
  Flatten(),
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
  for i in range(2, len(data)):
    params.append(data[i-2:i])
    results.append(data[i])

params, results = np.array(params), np.array(results)

model.fit(params, results, epochs=10, batch_size=10, verbose=1)

loss = model.evaluate(params, results)
print(f"Loss: {loss}")

predictions = model.predict(np.expand_dims(np.zeros((9, 2)), axis=0))
print(predictions)

model.save('/content/model.keras')
