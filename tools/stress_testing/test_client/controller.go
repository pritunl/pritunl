package main

import (
	"fmt"
	"os/exec"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"strings"
	"flag"
	"net/http"
)

const count = 128

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

	for i := 1; i <= count; i++ {
		cid, err := ExecOutput(
			"docker",
			"run",
			"-d",
			"--privileged",
			"-p", fmt.Sprintf("%d:%d", 4000 + i, 4000 + i),
			"test_client",
			"--num", fmt.Sprintf("%d", i),
		)
		if err != nil {
			panic(err)
		}

		cid = strings.TrimSpace(cid)
		fmt.Println(cid)
		cids = append(cids, cid)
	}

	fmt.Println("\n")

	signals := make(chan os.Signal, 1)
	signal.Notify(signals, os.Interrupt)
	signal.Notify(signals, syscall.SIGTERM)
	<-signals

	waiter := sync.WaitGroup{}
	waiter.Add(len(cids))
	for _, cid := range cids {
		go func(cid string) {
			ExecOutput("docker", "stop", cid)
			ExecOutput("docker", "rm", cid)
			println(cid)
			waiter.Done()
		}(cid)
	}
	waiter.Wait()
}

func Start() {
	waiter := sync.WaitGroup{}
	waiter.Add(count)

	for i := 1; i <= count; i++ {
		go func(i int) {
			resp, err := http.Get(
				fmt.Sprintf("http://localhost:%d/start", 4000 + i))
			if err != nil {
				return
			}

			if resp.StatusCode != 200 {
				panic(fmt.Sprintf("failed to start %d", i))
			}

			fmt.Println(fmt.Sprintf("http://localhost:%d/start", 4000 + i))

			waiter.Done()
		}(i)
	}

	waiter.Wait()
}

func Stop() {
	waiter := sync.WaitGroup{}
	waiter.Add(count)

	for i := 1; i <= count; i++ {
		go func(i int) {
			resp, err := http.Get(
				fmt.Sprintf("http://localhost:%d/stop", 4000 + i))
			if err != nil {
				return
			}

			if resp.StatusCode != 200 {
				panic(fmt.Sprintf("failed to stop %d", i))
			}

			fmt.Println(fmt.Sprintf("http://localhost:%d/stop", 4000 + i))

			waiter.Done()
		}(i)
	}

	waiter.Wait()
}

func Ping() {
	waiter := sync.WaitGroup{}
	waiter.Add(count)

	for i := 1; i <= count; i++ {
		go func(i int) {
			resp, err := http.Get(
				fmt.Sprintf("http://localhost:%d/ping", 4000 + i))
			if err != nil {
				return
			}

			if resp.StatusCode != 200 {
				panic(fmt.Sprintf("failed to ping %d", i))
			}

			fmt.Println(fmt.Sprintf("http://localhost:%d/ping", 4000 + i))

			waiter.Done()
		}(i)
	}

	waiter.Wait()
}

func Download() {
	waiter := sync.WaitGroup{}
	waiter.Add(count)

	for i := 1; i <= count; i++ {
		go func(i int) {
			resp, err := http.Get(
				fmt.Sprintf("http://localhost:%d/download", 4000 + i))
			if err != nil {
				return
			}

			if resp.StatusCode != 200 {
				panic(fmt.Sprintf("failed to download %d", i))
			}

			fmt.Println(fmt.Sprintf("http://localhost:%d/download", 4000 + i))

			waiter.Done()
		}(i)
	}

	waiter.Wait()
}

func main() {
	flag.Parse()

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
