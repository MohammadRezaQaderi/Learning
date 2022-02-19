package handler

import (
	"fmt"
	"github.com/MohammadRezaQaderi/Learning/Golang/echo/request"
	"github.com/labstack/echo/v4"
	"log"
	"net/http"
)

type Hello struct {
	From string
}

func (h Hello) User(c echo.Context) error {
	value := c.Param("username")

	log.Println(value)

	// nolint: wrapcheck
	return c.NoContent(http.StatusNoContent)
}

func (h Hello) Get(c echo.Context) error {
	if value := c.QueryParam("hello"); value != "" {
		log.Println(value)
	}

	return c.JSON(http.StatusOK, fmt.Sprintf("Hello To you from %s", h.From))
}

func (h Hello) Post(c echo.Context) error {
	var req request.Name

	if err := c.Bind(&req); err != nil {
		return echo.NewHTTPError(http.StatusBadRequest, err.Error())
	}
	log.Println(req)
	if req.Count == nil {
		log.Println("There is no Count")
	} else {
		log.Printf("There is a count %d", *req.Count)
	}

	// nolint: wrapcheck
	return c.String(http.StatusOK, fmt.Sprintf("Hello to %v from %s", req, h.From))
}
