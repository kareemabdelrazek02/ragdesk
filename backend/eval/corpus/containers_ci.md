# Containers and Continuous Integration

A Docker image packages an application with its dependencies so it runs the same way on every machine. A multi-stage Dockerfile builds the application in one stage and copies only the result into a small runtime image, which reduces image size and attack surface.

Docker Compose describes several services, such as an API, a database and a frontend, in one YAML file and starts them together on a shared network.

Continuous integration runs automated checks on every push or pull request. A typical GitHub Actions workflow installs dependencies, runs a linter, executes unit and integration tests, and builds the container image. A failing check blocks the merge, which keeps the main branch releasable.

Test coverage reports show which lines the test suite exercises, but high coverage alone does not guarantee that the assertions are meaningful.
