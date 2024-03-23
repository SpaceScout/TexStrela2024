ЦЕЛЕВАЯ СИСТЕМА Windows 10 22H2 
Проект написан на django, так что для работы понадобится python 3.11.7
ВАЖНО ЧТОБЫ В ПУТИ ЗАПУСКА САЙТА НЕ БЫЛО РУССКИХ СИМВОЛОВ

1.1 НАСТРОЙКА ОКРУЖЕНИЯ
Для работы вам нужно установить python, конкретно 3.11.7 (с другими версиями может выдать ошибку). Сделать это можно по ссылке: https://www.python.org/downloads/release/python-3117/. Затем вы должны создать venv такой же версией как и python. Откройте cmd из папки проекта (в папке /TexStrela2024/) и выполните команду:
	python -m venv venv.

1.2 Вы должны активировать venv, чтобы в консоли перед строкой вода писалось (venv). Для этого запустите консоль в папке /TexStrela2024/ и введите следующие команды: 
	cd .\venv\
	cd .\Scripts\
	.\activate

1.3 Затем вы должны скачать все библиотеки из файла requirments.txt. Выполните команду: pip install -r requirments.txt, находясь в папке /TexStrela2024/.

2.1 ИМПОРТ БД 
У вас должен быть доступ к запущенному серверу MySql. Можно использовать phpMyAdmin для более простого экспорта бд. 
 1. Создайте базу данных под названием tex-strela. Нажмите на нее. 
 2. В меню слева сверху нажмите на импорт. 
 3. В открывшемся меню выберите файл из папки, и внизу нажмите ИМПОРТ. По завершению у вас должны появится полная база данных. 

	2.1.1 Если у вас нет PhpMyAdmin, бд можно импортировать либо с помощью вашего сервера mysql, либо командами. Создайте 	новую бд tex-strela. Напишите в командной строке следующее 		(можете добавить -p и указать свой пароль), 	заменяя десктоп на расположение нашей папки, и меняя путь к mysql в начале:
	C:\xampp\mysql\bin\mysql -u root tex-strela < C:\Users\Space\Desktop\SPASTERS\tex-strela.sql

2.2 ПОДКЛЮЧЕНИЕ К БД ПРИ ЗАПУСКЕ
Подключение происходит к root пользователю без пароля. Если у вас другой пользователь БД, вы можете изменить подключение в файле settings.py (77-86 строки). Он находится в TexStrela2024\gallery\gallery\settings.py.	

2.3. Если вы импортнули бд, то пропустите этот пункт. Создайте новую бд tex-strela. После создания необходимо произвести миграции (создать таблицы в бд). Убедитесь что у вас запущен venv и перейдите в папку с файлом manage.py (от корня напишите cd gallery). Вводим следующие команды:
	1) cd gallery
	1) py manage.py makemigrations
	2) py manage.py makemigrations mainApp
	3) py manage.py migrate

3. После скачивания всех библиотек и создания бд, вы можете запустить сервер командами:
	1) Если вы пропустили 2.3 то: cd gallery
	2) py manage.py runserver
После докачки еще нескольких библиотек, сайт запустится.

ССЫЛКА НА ГИТХАБ: https://github.com/SpaceScout/TexStrela2024/releases

ВАЖНО
Для распознавания лиц используется нейронная сеть. Во время вызова ее первый раз(первый запуск функции распознавания) Она может около 2-3 минут скачать необходимые ей компоненты. Скачивать она их будет по пути: C:\Users\Space\.deepface\weights.