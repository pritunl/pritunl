package main

import (
	"flag"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"os/signal"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"
)

const count = 500

var host = 0

func ExecOutput(name string, args ...string) (output string, err error) {
	cmd := exec.Command(name, args...)

	outputByt, err := cmd.CombinedOutput()
	if err != nil {
		return
	}
	output = string(outputByt)

	return
}

func Setup() {
	cids := []string{}

	defer func() {
		waiter := sync.WaitGroup{}
		waiter.Add(len(cids))
		for _, cid := range cids {
			go func(cid string) {
				ExecOutput("docker", "kill", cid)
				ExecOutput("docker", "rm", cid)
				println(cid)
				waiter.Done()
			}(cid)

			time.Sleep(5 * time.Millisecond)
		}
		waiter.Wait()
	}()

	for i := 1 + (host * count); i <= count+(host*count); i++ {
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
			panic(err)
		}

		cid = strings.TrimSpace(cid)
		fmt.Println(cid)
		cids = append(cids, cid)

		time.Sleep(5 * time.Millisecond)
	}

	fmt.Println("\n")

	signals := make(chan os.Signal, 1)
	signal.Notify(signals, os.Interrupt)
	signal.Notify(signals, syscall.SIGTERM)
	<-signals
}

func Start() {
	waiter := sync.WaitGroup{}
	waiter.Add(count)

	for i := 1 + (host * count); i <= count+(host*count); i++ {
		go func(i int) {
			resp, err := http.Get(
				fmt.Sprintf("http://localhost:%d/start", 4000+i))
			if err != nil {
				return
			}

			if resp.StatusCode != 200 {
				panic(fmt.Sprintf("failed to start %d", i))
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

	for i := 1 + (host * count); i <= count+(host*count); i++ {
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

	for i := 1 + (host * count); i <= count+(host*count); i++ {
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

	for i := 1 + (host * count); i <= count+(host*count); i++ {
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
	flag.Parse()

	hostStr := os.Getenv("HOST")
	if hostStr != "" {
		host, _ = strconv.Atoi(hostStr)
	}

	switch flag.Arg(0) {
	case "setup":
		Setup()
	case "start":
		Start()
	case "stop":
		Stop()
	case "ping":
		Ping()
	case "download":
		Download()
	}
}
