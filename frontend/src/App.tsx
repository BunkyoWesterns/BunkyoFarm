import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css'
import '@mantine/charts/styles.css'
import '@mantine/dates/styles.css';
import '@mantine/dropzone/styles.css';

import { Notifications } from '@mantine/notifications';
import { LoadingOverlay, MantineProvider, Title } from '@mantine/core';
import { LoginProvider } from '@/components/LoginProvider';
import { Routes, Route, BrowserRouter } from "react-router-dom";
import { useGlobalStore } from './utils/stores';
import { statusQuery } from './utils/queries';
import { HomePage } from './components/screens/HomePage';
import { MainLayout } from './components/MainLayout';

export default function App() {

    const loadingStatus = useGlobalStore((store) => store.loading)
  
    const status = statusQuery()

    return (
        <MantineProvider defaultColorScheme='dark'>
            <Notifications />
            <LoadingOverlay visible={loadingStatus || status.isLoading } zIndex={10} overlayProps={{ radius: "sm", blur: 2 }} />
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
