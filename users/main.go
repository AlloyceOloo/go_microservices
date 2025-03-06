package main

import (
    "log"
    "users/src/database"
    "github.com/gofiber/fiber/v3"
    "users/src/database"
    "users/src/routes"

)

func main() {
    database.Connect()
    database.AutoMigrate()

    app := fiber.New()

    app.Use(cors.New(cors.Config{
        AllowCredentials: true,
    }))

    routes.Setup(app)

    // Start the server on port 3000
    log.Fatal(app.Listen(":8000"))
}