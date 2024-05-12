import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css'

import { Notifications } from '@mantine/notifications';
import { AppShell, Box, Container, Image, LoadingOverlay, MantineProvider, Space, Title } from '@mantine/core';
import { LoginProvider } from '@/components/LoginProvider';
import { Routes, Route, BrowserRouter } from "react-router-dom";
import { LogoutButton } from '@/components/Buttons';
import { useGlobalStore, useTokenStore } from './utils/stores';

export default function App() {

  const loadingStatus = useGlobalStore((store) => store.loading)
  const setToken = useTokenStore((store) => store.setToken)
  const header = useGlobalStore((store) => store.header)

  return (
    <MantineProvider defaultColorScheme='dark'>
      <Notifications />
      <LoadingOverlay visible={loadingStatus} zIndex={1000} overlayProps={{ radius: "sm", blur: 2 }} />
      <LoginProvider>
        <AppShell
          header={{ height: 60 }}
          navbar={{
            width: 300,
            breakpoint: 'sm',
            collapsed: { desktop: true, mobile: true },
          }}
        >
          <AppShell.Header>
            <Box style={{
              display: "flex",
              height: "100%",
              alignItems: "center"
            }}>
              <Space w="md" />
              <Image src="/logo.png" alt="Splitify Logo" width={30} height={30} />
              <Space w="xs" />
              <Title order={2}>
                Exploit Farm 👾
              </Title>
              <Box style={{ flexGrow: 1 }} />
              {header}
              <LogoutButton onClick={() => setToken("")} />
              <Space w="md" />
            </Box>
          </AppShell.Header>
          <AppShell.Main>
          <Container>
              <BrowserRouter>
                  <Routes>
                    <Route path="/" element={<></>} />
                    <Route path="*" element={<Title order={1}>404 Not Found</Title>} />
                  </Routes>
              </BrowserRouter>
            </Container>
          </AppShell.Main>
        </AppShell>
      </LoginProvider>
    </MantineProvider>
  )
}
