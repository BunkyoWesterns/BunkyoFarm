import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css'

import { Notifications } from '@mantine/notifications';
import { AppShell, Box, Container, Image, LoadingOverlay, MantineProvider, Space, Title } from '@mantine/core';
import { LoginProvider } from '@/components/LoginProvider';
import { Routes, Route, BrowserRouter } from "react-router-dom";
import { LogoutButton, OptionButton } from '@/components/Buttons';
import { useGlobalStore, useTokenStore } from './utils/stores';
import { statusQuery } from './utils/queries';
import { HomePage } from './components/HomePage';

export default function App() {

  const loadingStatus = useGlobalStore((store) => store.loading)
  const setToken = useTokenStore((store) => store.setToken)
  const header = useGlobalStore((store) => store.header)
  const status = statusQuery()

  return (
    <MantineProvider defaultColorScheme='dark'>
      <Notifications />
      <LoadingOverlay visible={loadingStatus || status.isLoading} zIndex={1000} overlayProps={{ radius: "sm", blur: 2 }} />
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
              <Image src="/logo.png" alt="ExploitFarm Logo" width={50} height={50} style={{marginLeft:5}}/>
              <Space w="xs" />
              <Title order={2}>
                Exploit Farm
              </Title>
              <Box style={{ flexGrow: 1 }} />
              {header}
              <OptionButton onClick={() =>{}} />
              <Space w="md" />
              {status.data?.config?.AUTHENTICATION_REQUIRED?<LogoutButton onClick={() => {
                setToken(null)
                status.refetch()
              }} />:null}
              <Space w="md" />
            </Box>
          </AppShell.Header>
          <AppShell.Main>
          <Container fluid>
              <BrowserRouter>
                  <Routes>
                    <Route path="/" element={<HomePage />} />
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
