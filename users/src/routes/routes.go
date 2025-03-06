package routes

import (
	"github.com/gofiber/fiber/v3"
)

func Setup(app *fiber.App) {
	api := app.Group("api")

	api.Post("register", controllers.Register)
	//api.Post("login", controllers.Login)

	//authenticated := api.Use(middlewares.IsAuthenticated)
	
	//authenticated.Get("user", controllers.User)
	//authenticated.Post("logout", controllers.Logout)
	//authenticated.Put("users/info", controllers.UpdateInfo)
	//authenticated.Put("users/password", controllers.UpdatePassword)


}
