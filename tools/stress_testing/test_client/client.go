package main

import (
	"fmt"
	"sync"
	"bufio"
	"os"
	"os/exec"
	"flag"
	"github.com/gin-gonic/gin"
)

var (
	cmd *exec.Cmd
	num int
	output = ""
)

const (
	host = "10.154.0.2"
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

func run() (err error) {
	if cmd != nil {
		return
	}

	output = ""
	lock := sync.Mutex{}

	cmd = exec.Command("openvpn", "--float", "--config",
		fmt.Sprintf("confs/user_%05d.ovpn", num))
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return
	}
	stderr, err := cmd.StderrPipe()
	if err != nil {
		return
	}

	stdoutRdr := bufio.NewReader(stdout)
	go func() {
		for {
			line, _, err := stdoutRdr.ReadLine()
			if err != nil {
				return
			}
			lock.Lock()
			output += string(line) + "\n"
			lock.Unlock()
		}
	}()

	stderrRdr := bufio.NewReader(stderr)
	go func() {
		for {
			line, _, err := stderrRdr.ReadLine()
			if err != nil {
				return
			}
			lock.Lock()
			output += string(line) + "\n"
			lock.Unlock()
		}
	}()

	cmd.Start()

	go func() {
		cmd.Wait()
		cmd = nil
	}()

	return
}

func main() {
	numPtr := flag.Int("num", 1, "client number")
	flag.Parse()
	num = *numPtr

	r := gin.Default()

	r.GET("/start", func(c *gin.Context) {
		err := run()
		if err != nil {
			c.String(500, err.Error())
			return
		}
		c.String(200, "started")
	})

	r.GET("/stop", func(c *gin.Context) {
		if cmd != nil && cmd.Process != nil {
			err := cmd.Process.Signal(os.Interrupt)
			if err != nil {
				c.String(500, err.Error())
				return
			}
		}
		c.String(200, "stopped")
	})

	r.GET("/output", func(c *gin.Context) {
		c.String(200, output)
	})

	r.GET("/route", func(c *gin.Context) {
		outpt, err := ExecOutput("route", "-n")
		if err != nil {
			c.String(500, err.Error())
			return
		}

		c.String(200, outpt)
	})

	r.GET("/download", func(c *gin.Context) {
		outpt, err := ExecOutput("wget", "-O", "/dev/null",
			fmt.Sprintf("http://%s:8000/test", host))
		if err != nil {
			c.String(500, err.Error())
			return
		}

		c.String(200, outpt)
	})

	r.GET("/ping", func(c *gin.Context) {
		outpt, err := ExecOutput("ping", "-c", "3", "-W", "3", host)
		if err != nil {
			c.String(500, err.Error())
			return
		}

		c.String(200, outpt)
	})

	r.Run(fmt.Sprintf(":%d", 4000 + num))
}
