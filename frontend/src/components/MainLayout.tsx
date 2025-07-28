import { Alert, AppShell, Box, Container, Divider, Image, Modal, Space, Title } from "@mantine/core"
import { EngineButton, LogoutButton, OptionButton } from "./inputs/Buttons"
import { useGlobalStore, useTokenStore } from "@/utils/stores"
import { useState } from "react"
import { statusQuery } from "@/utils/queries"
import { SetupScreen } from "@/components/screens/SetupScreen"
import { OptionScreen } from "@/components/screens/OptionScreen"

export const MainLayout = ({ children }: { children: any }) => {
    const setToken = useTokenStore((store) => store.setToken)
    const { header, errorMessage } = useGlobalStore()
    const status = statusQuery()
    const [openSetup, setOpenSetup] = useState(false)
    const [openOptions, setOpenOptions] = useState(false)

    return <AppShell
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
                    <Image src="/logo.png" alt="ExploitFarm Logo" style={{marginLeft:5, width:"50px"}}/>
                    <Space w="xs" />
                    <Title order={2}>
                        Exploit Farm
                    </Title>
                    <Box style={{ flexGrow: 1 }} />
                    {header}
                    <EngineButton onClick={() => setOpenSetup(true)} />
                    <Space w="md" />
                    <OptionButton onClick={()=>setOpenOptions(true)} />
                    <Space w="md" />
                    {status.data?.config?.AUTHENTICATION_REQUIRED?<>
                        <LogoutButton onClick={() => {
                            setToken(null)
                            status.refetch()
                        }} />
                        <Space w="md" />
                    </>:null}
                </Box>
            </AppShell.Header>
            <AppShell.Main>
            <Container fluid>
                {errorMessage?<Alert
                    title={errorMessage.title}
                    color={errorMessage.color}
                    style={{width: "100%", height:"100%", display:"flex"}}
                    my="md"
                >
                    {errorMessage.message}
                </Alert>:null}

                {children}

                <Divider />
                <Box className='center-flex' style={{ width: "100%", height:80 }} >
                    <span>Made with ❤️ and 🚩 by <a href="https://pwnzer0tt1.it" target='_blank'>Pwnzer0tt1</a></span>
                </Box>
                <Divider />

            </Container>
            
            <Modal
                opened={openSetup}
                onClose={()=>setOpenSetup(false)}
                title="Setup Editor ⚙️"
                centered
                fullScreen
                closeOnClickOutside={false}
                closeOnEscape={false}
            >
                <SetupScreen editMode onSubmit={()=>setOpenSetup(false)}/>
            </Modal>
            <Modal
                opened={openOptions}
                onClose={()=>setOpenOptions(false)}
                title="Options ⚙️"
                centered
                fullScreen
                closeOnClickOutside={false}
                closeOnEscape={false}
            >
                <OptionScreen />
            </Modal>
        </AppShell.Main>
    </AppShell>
}