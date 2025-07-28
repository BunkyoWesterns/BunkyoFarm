import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css'
import '@mantine/charts/styles.css'
import '@mantine/dates/styles.css';
import '@mantine/dropzone/styles.css';
import '@mantine/code-highlight/styles.css';

import { notifications, Notifications } from '@mantine/notifications';
import { LoadingOverlay, MantineProvider, Title } from '@mantine/core';
import { LoginProvider } from '@/components/LoginProvider';
import { Routes, Route, BrowserRouter } from "react-router";
import { useGlobalStore, useTokenStore } from './utils/stores';
import { statusQuery } from './utils/queries';
import { HomePage } from './components/screens/HomePage';
import { MainLayout } from './components/MainLayout';
import { useEffect } from 'react';
import { DEBOUNCED_SOCKET_IO_CHANNELS, socket_io, SOCKET_IO_CHANNELS, sockIoChannelToQueryKeys } from './utils/net';
import { useQueryClient } from '@tanstack/react-query';
import { useDebouncedCallback } from '@mantine/hooks'
import { CodeHighlightAdapterProvider, stripShikiCodeBlocks } from '@mantine/code-highlight';
import { CodeHighlightAdapter } from 'node_modules/@mantine/code-highlight/lib/CodeHighlightProvider/CodeHighlightProvider';


// Shiki requires async code to load the highlighter
async function loadShiki() {
  const { createHighlighter } = await import('shiki');
  const shiki = await createHighlighter({
    langs: ['python'],
    themes: ['one-dark-pro', 'one-light']
  });

  return shiki;
}

// Pass this adapter to CodeHighlightAdapterProvider component
export const customShikiAdapter: CodeHighlightAdapter = {
  // loadContext is called on client side to load shiki highlighter
  // It is required to be used if your library requires async initialization
  // The value returned from loadContext is passed to createHighlighter as ctx argument
  loadContext: loadShiki,

  getHighlighter: (ctx) => {
    if (!ctx) {
      return ({ code }) => ({ highlightedCode: code, isHighlighted: false });
    }

    return ({ code, language, colorScheme }) => ({
      isHighlighted: true,
      // stripShikiCodeBlocks removes <pre> and <code> tags from highlighted code
      highlightedCode: stripShikiCodeBlocks(
        ctx.codeToHtml(code, {
          lang: language,
          theme: colorScheme === 'dark' ? 'one-dark-pro' : 'one-light',
        })
      ),
    });
  },
};

export default function App() {

    const queryClient = useQueryClient()
    const { setErrorMessage, loading:loadingStatus } = useGlobalStore()
    const { loginToken } = useTokenStore()

    const debouncedCalls = DEBOUNCED_SOCKET_IO_CHANNELS.map((channel) => (
        useDebouncedCallback(() => {
            sockIoChannelToQueryKeys(channel).forEach((data) =>
                queryClient.invalidateQueries({ queryKey: data })
            )
        }, 3000)
    ))
    
    useEffect(() => {
        SOCKET_IO_CHANNELS.forEach((channel) => {
            socket_io.on(channel, (_data) => {
                if (DEBOUNCED_SOCKET_IO_CHANNELS.includes(channel)) {
                    debouncedCalls[DEBOUNCED_SOCKET_IO_CHANNELS.indexOf(channel)]()
                } else {
                    sockIoChannelToQueryKeys(channel).forEach((data) =>
                        queryClient.invalidateQueries({ queryKey: data })
                    )
                }
            })
        })
        socket_io.on("connect_error", (err) => {
            setErrorMessage({
                title: "BACKEND SEEMS DOWN!",
                message: "Can't connect to backend APIs: " + err.message,
                color: "red"
            })
        });
        
        let first_time = true
        socket_io.on("connect", () => {
            if (socket_io.connected) {
                setErrorMessage(null)
                if (!first_time) {
                    queryClient.resetQueries({ queryKey: [] })
                    notifications.show({
                        id: "connected-backend",
                        title: "Connected to the backend!",
                        message: "Successfully connected to the backend!",
                        color: "blue",
                        icon: "🚀",
                    })
                }
            }
            first_time = false
        });
        return () => {
            SOCKET_IO_CHANNELS.forEach((channel) => {
                socket_io.off(channel)
            })
            socket_io.off("connect_error")
        }
    }, [])


    useEffect(() => {
        socket_io.auth = { token: loginToken }
        socket_io.disconnect()
        socket_io.connect()
    }, [loginToken])

    const status = statusQuery()

    return (
        <MantineProvider defaultColorScheme='dark'>
            <CodeHighlightAdapterProvider adapter={customShikiAdapter}>
                <Notifications />
                <LoadingOverlay visible={loadingStatus || status.isLoading} zIndex={10} overlayProps={{ radius: "sm", blur: 2 }} />
                <LoginProvider>
                    <BrowserRouter>
                        <Routes>
                            <Route path="/" element={<HomePage />} />
                            <Route path="/:page" element={<HomePage />} />
                            <Route path="*" element={<MainLayout><Title order={1}>404 Not Found</Title></MainLayout>} />
                        </Routes>
                    </BrowserRouter>
                </LoginProvider>
            </CodeHighlightAdapterProvider>
        </MantineProvider>
    )
}
