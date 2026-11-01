# Kubernetes Troubleshooting: Backend API Returns 500 Because the Database Table Is Missing

## 1. What Happened?

After resolving the previous deployment errors, I opened the frontend application and clicked the button. However, I was not getting any output.

To troubleshoot this issue, I checked the logs of both the frontend and backend Pods.

The backend logs showed that the API request was failing because the required `users` table was not present in PostgreSQL.

## 2. Check the Backend Pod Logs

I ran the following command to check the backend logs:

```bash
kubectl logs claimiq-backend-864447c689-rdxqd -n claimiq
```

### Error Received

```text
* Serving Flask app 'app'
* Debug mode: off

WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.

* Running on all addresses (0.0.0.0)
* Running on http://127.0.0.1:5000
* Running on http://10.244.1.147:5000
Press CTRL+C to quit

[2026-10-15 01:57:47,554] ERROR in app: Exception on /users [GET]

Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/flask/app.py", line 1511, in wsgi_app
    response = self.full_dispatch_request()
  File "/usr/local/lib/python3.12/site-packages/flask/app.py", line 919, in full_dispatch_request
    rv = self.handle_user_exception(e)
  File "/usr/local/lib/python3.12/site-packages/flask/app.py", line 917, in full_dispatch_request
    rv = self.dispatch_request()
  File "/usr/local/lib/python3.12/site-packages/flask/app.py", line 902, in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)
  File "/app/app.py", line 38, in users
    cursor.execute("SELECT id, name FROM users ORDER BY id")

psycopg2.errors.UndefinedTable: relation "users" does not exist

LINE 1: SELECT id, name FROM users ORDER BY id
                             ^

10.244.1.174 - - [15/Oct/2026 01:57:47] "GET /users HTTP/1.1" 500 -
```

The same error appeared repeatedly when the `/users` API endpoint was called.

## 3. Why Did This Error Occur?

The important part of the error is:

```text
psycopg2.errors.UndefinedTable: relation "users" does not exist
```

This means the backend application tried to execute the following SQL query:

```sql
SELECT id, name FROM users ORDER BY id;
```

However, PostgreSQL could not find a table named `users`.

The backend application was running, and it was able to execute a database query. But the required `users` table had not been created in PostgreSQL.

Because the table was missing, the API returned an HTTP `500 Internal Server Error`, and the frontend did not receive the expected data to display.

**Reason:** The required database table and its data were not initialized in PostgreSQL.

## 4. Resolution: Create a Kubernetes Job to Initialize the Database

To resolve this issue, I decided to create a Kubernetes Job that runs the database initialization script.

The Job runs the `init.sql` script, which creates the required database tables and data for the application to work.

A Kubernetes Job is used to run a task that completes successfully and then stops. Unlike a Deployment, it does not keep a container running continuously.

### How the Job Works

1. When the application is deployed, Kubernetes starts the database initialization Job.
2. The Job executes the `init.sql` script against PostgreSQL.
3. The script creates the required database tables and inserts the required data.
4. After the script completes successfully, the Job finishes.
5. The Job's container stops because its task is complete.

This ensures that the database initialization task is executed as a separate task instead of being run continuously inside the application container.

## 5. Key Takeaways

- When the frontend does not display the expected output, check the frontend and backend Pod logs.
- The backend logs help identify errors occurring while processing API requests.
- `psycopg2.errors.UndefinedTable` means the requested database table does not exist.
- In this case, the `/users` API failed because the `users` table was missing in PostgreSQL.
- A missing database table can cause the backend API to return HTTP `500`.
- A Kubernetes Job can be used to execute a database initialization script.
- The `init.sql` script creates the required tables and data.
- A Job completes its task and then stops; it does not run continuously like a Deployment.

**Remember:** If the application is running but an API returns an error, check the backend logs and verify that the required database tables and data have been initialized.
