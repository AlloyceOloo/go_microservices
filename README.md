![use case exp](exp.png)

This project demonstrates a microservices-based architecture designed with scalability and modularity in mind. The system is containerized with Docker and leverages Apache Kafka for asynchronous messaging between services.</n>

<h2>Services</h2></n>
Admin, Ambassador, and Checkout Frontends:
Interface layers interacting with the core application logic. </n>

<h2>Core Application Service (Go + Docker):</h2></n>
Central backend logic written in Go, containerized using Docker. It handles data persistence via MySQL and communicates with other microservices through Kafka.</n>

<h2>Email Microservice (Go + Docker):</h2></n>
A dedicated service for sending transactional emails. It consumes messages from Kafka to trigger email events asynchronously.</n>

<h2>Integration</h2></n>
Database: MySQL is used for structured data storage.

Kafka: Manages asynchronous communication between services, ensuring loose coupling and high throughput.

Docker: All services are containerized for easier deployment and consistency across environments.

