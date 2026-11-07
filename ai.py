import matplotlib.pyplot as plt
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score

print("1. Загрузка встроенного датасета цифр...")
digits = load_digits()

X = digits.data
y = digits.target

# ТУТ ИСПРАВЛЕНО НА test_size
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("2. Создание архитектуры нейросети...")
# Оптимизатор 'adam' автоматически подберет идеальную скорость обучения
mlp = MLPClassifier(hidden_layer_sizes=(50,), max_iter=500, alpha=1e-4,
                    solver='adam', verbose=True, random_state=1)

print("3. Начало обучения нейросети...")
mlp.fit(X_train, y_train)

print("\n4. Проверка точности...")
predictions = mlp.predict(X_test)

accuracy = accuracy_score(y_test, predictions)
print(f"Точность обученной нейросети: {accuracy * 100:.2f}%")

# Берем первую картинку из тестовой выборки для демонстрации
first_test_image = X_test[0].reshape(8, 8)
real_label = y_test[0]
predicted_label = predictions[0]

# Показываем ее на экране
plt.gray()
plt.matshow(first_test_image) 
print(f"\nРеальная цифра на проверочной картинке: {real_label}")
print(f"Нейросеть считает, что это: {predicted_label}")
print("Закройте появившееся графическое окно, чтобы завершить программу.")
plt.show()

import pickle

# Сохраняем "мозг" обученной нейросети в файл
with open('c:/gith/lin/my_digits_model.pkl', 'wb') as f:
    pickle.dump(mlp, f)
print("\n[ИИ]: Нейросеть успешно сохранена в файл 'my_digits_model.pkl'!")
