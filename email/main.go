package main

import (
	"fmt"
	"time"
	"encoding/json"
	"net/smtp"
	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
)


func main() {

	consumer, err := kafka.NewConsumer(&kafka.ConfigMap{
		"bootstrap.servers": "pkc-921jm.us-east-2.aws.confluent.cloud:9092",
		"security.protocol": "SASL_SSL",
		"sasl.username": "NK4AXYUASJXEZKKK",
		"sasl.password": "LGmltPhHp4wTu0dVrZLxJqSWlx1K2jmlROdElaspDQFLixCCJAFjCQ6prKPOkf8N",
		"sasl.mechanisms": "PLAIN",
		"group.id":          "myGroup",
		"auto.offset.reset": "earliest",
	})

	if err != nil {
		panic(err)
	}

	consumer.SubscribeTopics([]string{"default"}, rebalanceCb:nil)

	for {
		msg, err := consumer.ReadMessage(timeout: -1)
		if err != nil {
			// The clinet automatically tries to recover from errors
			fmt.Printf(format: "Consumer error: %v (%v)\n", err, msg)
			return
		}

		fmt.Printf(format: "Message on %s : %s\n", msg.TopicPartition, string(msg.Value))

		var message map[string]interface{}

		json.Unmarshal(msg.Value, &message)

		//host := os.Getenv("EMAIL_HOST")
		//port := os.Getenv("EMAIL_PORT")

		//auth := smtp.PlainAuth("", os.Getenv("EMAIL_USERNAME"), os.Getenv("EMAIL_PASSWORD"), host)

		ambassadorMessage := []byte(fmt.Sprintf("You earned $%f from the link #%s", message["ambassador_revenue"].(float64), message["code"]))

		smtp.SendMail(addr: "host.docker.internal:1025", a:nil, from:"no-reply@email.com", []string{message["ambassador_email"].(string)}, ambassadorMessage)

		adminMessage := []byte(fmt.Sprintf("Order #%f with a total of $%f has been completed", message["id"].(float64), message["admin_revenue"].(float64)))

		smtp.SendMail(addr: "host.docker.internal:1025", a:nil, from:"no-reply@email.com", []string{"admin@admin.com"}, adminMessage)
	}

	consumer.Close()

	//ambassadorMessage := []byte(fmt.Sprintf("You earned $%f from the link #%s", ambassadorRevenue, order.Code))

	//smtp.SendMail("host.docker.internal:1025", nil, "no-reply@email.com", []string{order.AmbassadorEmail}, ambassadorMessage)

	//adminMessage := []byte(fmt.Sprintf("Order #%d with a total of $%f has been completed", order.Id, adminRevenue))

	//smtp.SendMail("host.docker.internal:1025", nil, "no-reply@email.com", []string{"admin@admin.com"}, adminMessage)
	

}
