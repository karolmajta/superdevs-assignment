It's all standard python/django.

1. Clone and cd into checkout dir:

```
git clone git@github.com:karolmajta/superdevs-assignment.git
cd superdevs-assignment
```

2. Create and activate virtualenv. Install dependencies:

```
python -m venv virtualenv
source virtualenv/bin/activate
pip install -r requirements.txt
```

3. Cd into django project:

```
cd swbrowser
```

4. Run migrations:

```
python manage.py migrate
```

5. Run the dev server:

```
python manage.py runserver
```

