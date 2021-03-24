package utils

import (
	"log"
	"os"

	"github.com/charstal/schedule-extender/apis/config"
)

type LogType string

const (
	LOG_INFO    LogType = "[info]"
	LOG_WARNING LogType = "[warning]"
	LOG_ERROR   LogType = "[error]"
	LOG_FATAL   LogType = "[fatal]"
)

func LogWrite(lt LogType, msg string) {
	logFile, err := os.OpenFile(*config.LogPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
	print(*config.LogPath)
	if err != nil {
		panic("log file init error")
	}
	defer logFile.Close()
	logger := log.New(logFile, "", log.LstdFlags|log.Llongfile)
	logger.SetFlags(log.LstdFlags)
	logger.SetPrefix(string(lt))
	logger.Println(msg)
}
