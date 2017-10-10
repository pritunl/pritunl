package main

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"io/ioutil"
	"net/http"
	"os/exec"
	"strconv"
	"strings"
	"sync"
	"time"
)

const (
	commander = "scmd.pritunl.net"
	count     = 250
)

var (
	hostIndex = 0
	cids      []string
)

func ExecOutput(name string, args ...string) (output string, err error) {
	cmd := exec.Command(name, args...)

	outputByt, err := cmd.CombinedOutput()
	if err != nil {
		return
	}
	output = string(outputByt)

	return
}

func Event() {
	_, err := http.Get(
		fmt.Sprintf("http://%s:4000/event/%d", commander, hostIndex))
	if err != nil {
		panic(err)
	}
}

func Setup() {
	cids = []string{}

	for i := 1 + (hostIndex * count); i <= count+(hostIndex*count); i++ {
		for {
			cid, err := ExecOutput(
				"docker",
				"run",
				"-d",
				"--privileged",
				"-p", fmt.Sprintf("%d:%d", 4000+i, 4000+i),
				"test_client",
				"--num", fmt.Sprintf("%d", i),
			)
			if err != nil {
				time.Sleep(1 * time.Second)
				continue
			}

			cid = strings.TrimSpace(cid)
			fmt.Println(cid)
			cids = append(cids, cid)
			Event()

			break
		}

		time.Sleep(5 * time.Millisecond)
	}

	fmt.Println("\n")
}

func Close() {
	waiter := sync.WaitGroup{}
	waiter.Add(len(cids))
	for _, cid := range cids {
		go func(cid string) {
			ExecOutput("docker", "kill", cid)
			ExecOutput("docker", "rm", cid)
			println(cid)
			Event()
			waiter.Done()
		}(cid)

		time.Sleep(5 * time.Millisecond)
	}
	waiter.Wait()
}

func Start() {
	waiter := sync.WaitGroup{}
	waiter.Add(count)

	for i := 1 + (hostIndex * count); i <= count+(hostIndex*count); i++ {
		go func(i int) {
			fmt.Println(fmt.Sprintf("+http://localhost:%d/start", 4000+i))
			resp, err := http.Get(
				fmt.Sprintf("http://localhost:%d/start", 4000+i))
			if err != nil {
				return
			}
			defer resp.Body.Close()

			if resp.StatusCode != 200 {
				body, _ := ioutil.ReadAll(resp.Body)
				if !strings.Contains(string(body), "already started") {
					fmt.Println("already started")
				} else {
					panic(fmt.Sprintf("failed to start %d", i))
				}
			}

			fmt.Println(fmt.Sprintf("http://localhost:%d/start", 4000+i))

			waiter.Done()
		}(i)
	}

	waiter.Wait()
}

func Stop() {
	waiter := sync.WaitGroup{}
	waiter.Add(count)

	for i := 1 + (hostIndex * count); i <= count+(hostIndex*count); i++ {
		go func(i int) {
			resp, err := http.Get(
				fmt.Sprintf("http://localhost:%d/stop", 4000+i))
			if err != nil {
				return
			}

			if resp.StatusCode != 200 {
				panic(fmt.Sprintf("failed to stop %d", i))
			}

			fmt.Println(fmt.Sprintf("http://localhost:%d/stop", 4000+i))

			waiter.Done()
		}(i)
	}

	waiter.Wait()
}

func Ping() {
	waiter := sync.WaitGroup{}
	waiter.Add(count)

	for i := 1 + (hostIndex * count); i <= count+(hostIndex*count); i++ {
		go func(i int) {
			resp, err := http.Get(
				fmt.Sprintf("http://localhost:%d/ping", 4000+i))
			if err != nil {
				return
			}

			if resp.StatusCode != 200 {
				panic(fmt.Sprintf("failed to ping %d", i))
			}

			fmt.Println(fmt.Sprintf("http://localhost:%d/ping", 4000+i))

			waiter.Done()
		}(i)
	}

	waiter.Wait()
}

func Download() {
	waiter := sync.WaitGroup{}
	waiter.Add(count)

	for i := 1 + (hostIndex * count); i <= count+(hostIndex*count); i++ {
		go func(i int) {
			resp, err := http.Get(
				fmt.Sprintf("http://localhost:%d/download", 4000+i))
			if err != nil {
				return
			}

			if resp.StatusCode != 200 {
				panic(fmt.Sprintf("failed to download %d", i))
			}

			fmt.Println(fmt.Sprintf("http://localhost:%d/download", 4000+i))

			waiter.Done()
		}(i)
	}

	waiter.Wait()
}

func main() {
	resp, err := http.Get(
		fmt.Sprintf("http://%s:4000/register", commander))
	if err != nil {
		panic(err)
	}

	hostIndexStr, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		panic(err)
	}
	resp.Body.Close()
	hostIndex, _ = strconv.Atoi(string(hostIndexStr))

	r := gin.Default()

	r.GET("/setup", func(c *gin.Context) {
		go Setup()
		c.String(200, "")
	})

	r.GET("/close", func(c *gin.Context) {
		go Close()
		c.String(200, "")
	})

	r.GET("/start", func(c *gin.Context) {
		Start()
		c.String(200, "")
	})

	r.GET("/stop", func(c *gin.Context) {
		Stop()
		c.String(200, "")
	})

	r.GET("/ping", func(c *gin.Context) {
		Ping()
		c.String(200, "")
	})

	r.GET("/download", func(c *gin.Context) {
		Download()
		c.String(200, "")
	})

	r.Run(":3800")
}
