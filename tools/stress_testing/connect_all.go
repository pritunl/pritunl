package main

import (
	"fmt"
	"os/exec"
	"os"
	"os/signal"
	"syscall"
	"time"
)

const count = 256

func Exec(name string, args ...string) (cmd *exec.Cmd, err error) {
	cmd = exec.Command(name, args...)
	err = cmd.Start()

	return
}

func main() {
	cmds := []*exec.Cmd{}

	defer func() {
		for _, cmd := range cmds {
			cmd.Process.Signal(os.Interrupt)
		}
		for _, cmd := range cmds {
			cmd.Wait()
		}
	}()

	for i := 1; i <= count; i++ {
		cmd, err := Exec(
			"openvpn", fmt.Sprintf("user_%05d.ovpn", i),
		)
		if err != nil {
			panic(err)
		}
		cmds = append(cmds, cmd)

		time.Sleep(100 * time.Millisecond)
	}

	fmt.Println("\n")

	signals := make(chan os.Signal, 1)
	signal.Notify(signals, os.Interrupt)
	signal.Notify(signals, syscall.SIGTERM)
	<-signals
}
