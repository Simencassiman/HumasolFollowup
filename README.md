# Humasol Follow-up

This project contains a framework for the follow-up of Humasol projects. It is
intended to centralize and structure the registration of executed projects.
Furthermore, it provides the opportunity to automate some of the follow-up
tasks.

To contribute to this project please read the rest of this document to set up
a working environment.

The project is mainly split in two parts: a webapp to register projects and an
automation script to carry out follow-up jobs of the registered projects.

The webapp functionality is built using the [Flask](https://flask.palletsprojects.com/en/2.3.x/quickstart/)
framework. You can find a lot better and more detailed information in their
documentation.


## Setup

To start working on the project locally first of all clone the git repository
as follows.

```
git clone git@github.com:Simencassiman/HumasolFollowup.git
cd HumasolFollowup
```

And set up a virtual environment with all the python dependencies. Below are the
instructions to create a conda environment named humasol, but venv is a valid
alternative.
The project uses python 3.10, but later versions should be compatible as well.
Be sure to be inside the project directory to install the dependecies using the
requirements file.

```
conda create -n humasol python=3.10
conda activate humasol
pip install -r requirements.txt
```

Next, set up a PostgreSQL database for the project. You only need to create the
database itself, the schema will be created using the flask app. One way to do
this is using
[pgAdmin](https://www.pgadmin.org/docs/pgadmin4/7.6/getting_started.html).
This provides a handy GUI on top of the command line options to set up and
inspect databases. [This video](https://www.youtube.com/watch?v=Dd2ej-QKrWY)
shows you how to do it, but there are many sources that you can follow. The
name of the database will be necessary for the next section.

Finally, set up a file named .env with the environment variables following
env.example. These are the configuration variables that the app will read from
the environment (some of) which are not supposed to be distributed. The example
file contains a section on flask variables, which can be left as is for
development purposes. The database section contains a secret key, which should
be a random string of characters (although for a local version it's not too
important). A salt for the passwords, which should also be a random sequence of
characters. And the database URI, which will point the app to the newly created
database. The URI contains placeholders for the username, password and database
name, which should have all been used in the database setup section.
And lastly, a section for humasol variables. Currently there are initial values
for an admin account which will be created as a first user.


## Run locally

If everything is set up correctly, a debugging server can be started locally
as follows

```
flask run
```

This will serve the app on a local port which will be shown in the command line.
You should now be able to test out the webapp by using a browser to connect to
the local port.
