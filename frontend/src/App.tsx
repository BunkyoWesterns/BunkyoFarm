import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css'
import '@mantine/charts/styles.css'
import '@mantine/dates/styles.css';
import '@mantine/dropzone/styles.css';

import { notifications, Notifications } from '@mantine/notifications';
import { LoadingOverlay, MantineProvider, Title } from '@mantine/core';
import { LoginProvider } from '@/components/LoginProvider';
import { Routes, Route, BrowserRouter } from "react-router-dom";
import { useGlobalStore } from './utils/stores';
import { statusQuery } from './utils/queries';
import { HomePage } from './components/screens/HomePage';
import { MainLayout } from './components/MainLayout';
import { useEffect } from 'react';
import { DEBOUNCED_SOCKET_IO_CHANNELS, socket_io, SOCKET_IO_CHANNELS, sockIoChannelToQueryKeys } from './utils/net';
import { useQueryClient } from '@tanstack/react-query';
import { useDebouncedCallback } from '@mantine/hooks';

export default function App() {

    const queryClient = useQueryClient()
    const { setErrorMessage } = useGlobalStore()

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
                    queryClient.resetQueries({ queryKey: ["status"] })
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

    const loadingStatus = useGlobalStore((store) => store.loading)

    const status = statusQuery()

    return (
        <MantineProvider defaultColorScheme='dark'>
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
        </MantineProvider>
    )
}
