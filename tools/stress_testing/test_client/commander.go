package main

import (
	"fmt"
	"github.com/dropbox/godropbox/container/set"
	"github.com/gin-gonic/gin"
	"github.com/sethgrid/multibar"
	"net/http"
	"strconv"
	"strings"
	"sync"
	"time"
)

const (
	controllerSize = 250
)

var (
	hosts      = set.NewSet()
	hostsLock  = sync.Mutex{}
	bars       []*Bar
	barsWaiter sync.WaitGroup
)

type Bar struct {
	lock   sync.Mutex
	setter multibar.ProgressFunc
	size   int
	count  int
}

func (b *Bar) Incr() {
	b.lock.Lock()
	b.count += 1
	b.setter(b.count)
	if b.count >= controllerSize {
		barsWaiter.Done()
	}
	b.lock.Unlock()
}

func Print(msg string) {
	fmt.Printf("\n%s\n> ", msg)
}

func Setup() (err error) {
	bars = []*Bar{}
	barsWaiter = sync.WaitGroup{}
	barsWaiter.Add(hosts.Len())

	barContainer, err := multibar.New()
	if err != nil {
		return
	}

	for i := 0; i < hosts.Len(); i += 1 {
		bar := &Bar{
			size: controllerSize,
			setter: barContainer.MakeBar(
				controllerSize, fmt.Sprintf("HOST%03d:", i)),
		}
		bars = append(bars, bar)
	}

	go barContainer.Listen()

	for hostInf := range hosts.Iter() {
		host := hostInf.(string)

		resp, e := http.Get(
			fmt.Sprintf("http://%s:3800/setup", host))
		if e != nil {
			err = e
			return
		}
		if resp.StatusCode != 200 {
			err = fmt.Errorf("BAD STATUS %d ON %s",
				resp.StatusCode, host)
			return
		}
	}

	barsWaiter.Wait()
	time.Sleep(1 * time.Second)
	fmt.Println("SETUP COMPLETE")

	return
}

func Close() (err error) {
	bars = []*Bar{}
	barsWaiter = sync.WaitGroup{}

	barContainer, err := multibar.New()
	if err != nil {
		return
	}

	for i := 0; i < hosts.Len(); i += 1 {
		bar := &Bar{
			size: controllerSize,
			setter: barContainer.MakeBar(
				controllerSize, fmt.Sprintf("HOST%03d:", i)),
		}
		bars = append(bars, bar)
		barsWaiter.Add(1)
	}

	go barContainer.Listen()

	for hostInf := range hosts.Iter() {
		host := hostInf.(string)

		resp, e := http.Get(
			fmt.Sprintf("http://%s:3800/close", host))
		if e != nil {
			err = e
			return
		}
		if resp.StatusCode != 200 {
			err = fmt.Errorf("BAD STATUS %d ON %s",
				resp.StatusCode, host)
			return
		}
	}

	barsWaiter.Wait()
	time.Sleep(1 * time.Second)
	fmt.Println("CLOSE COMPLETE")

	return
}

func Start(delay int) (err error) {
	barContainer, err := multibar.New()
	if err != nil {
		return
	}

	setter := barContainer.MakeBar(hosts.Len(), "STATUS:")
	go barContainer.Listen()

	time.Sleep(100 * time.Millisecond)
	setter(0)

	i := 0
	for hostInf := range hosts.Iter() {
		host := hostInf.(string)

		_, err = http.Get(
			fmt.Sprintf("http://%s:3800/start", host))
		if err != nil {
			return
		}
		setter(i + 1)

		if i < hosts.Len()-1 {
			time.Sleep(time.Duration(delay) * time.Second)
		}

		i += 1
	}

	time.Sleep(1 * time.Second)
	fmt.Println("START COMPLETE")

	return
}

func Stop() (err error) {
	barContainer, err := multibar.New()
	if err != nil {
		return
	}

	setter := barContainer.MakeBar(hosts.Len(), "STATUS:")
	go barContainer.Listen()

	time.Sleep(100 * time.Millisecond)
	setter(0)

	i := 0
	for hostInf := range hosts.Iter() {
		host := hostInf.(string)

		resp, e := http.Get(
			fmt.Sprintf("http://%s:3800/stop", host))
		if e != nil {
			err = e
			return
		}
		if resp.StatusCode != 200 {
			err = fmt.Errorf("BAD STATUS %d ON %s",
				resp.StatusCode, host)
			return
		}

		setter(i + 1)

		i += 1
	}

	time.Sleep(1 * time.Second)
	fmt.Println("STOP COMPLETE")

	return
}

func Command(cmd, arg string) (err error) {
	switch cmd {
	case "status":
		for hostInf := range hosts.Iter() {
			host := hostInf.(string)

			fmt.Printf("HOST: %s\n", string(host))
		}
		fmt.Printf("%d HOSTS REGISTERED\n", hosts.Len())
		break
	case "setup":
		Setup()
		break
	case "close":
		Close()
		break
	case "start":
		delay, _ := strconv.Atoi(arg)
		Start(delay)
		break
	case "stop":
		Stop()
		break
	default:
		fmt.Println("UNKNOWN COMMAND")
	}

	return
}

func main() {
	r := gin.New()

	r.GET("/register", func(c *gin.Context) {
		addr := c.Request.RemoteAddr
		addr = addr[:strings.LastIndex(addr, ":")]

		hostsLock.Lock()
		hosts.Add(addr)
		index := hosts.Len() - 1
		hostsLock.Unlock()

		Print(fmt.Sprintf("%d HOSTS REGISTERED", index+1))

		c.String(200, fmt.Sprintf("%v", index))
	})

	r.GET("/event/:index", func(c *gin.Context) {
		hostIndex, _ := strconv.Atoi(c.Param("index"))
		go bars[hostIndex].Incr()
		c.String(200, "")
	})

	go r.Run(":4000")

	time.Sleep(1 * time.Second)

	for {
		cmd := ""
		arg := ""
		fmt.Print("> ")
		fmt.Scanln(&cmd, &arg)

		err := Command(cmd, arg)
		if err != nil {
			panic(err)
		}
	}
}
