import { Box, Container, Space } from "@mantine/core"
import { WelcomeTitle } from "./WelcomeTitle"


export const SetupScreen = () => {
    return <Container>
        <Space h="xl" />
        <WelcomeTitle description="Exploit farm is in setup mode ⚙️, insert all the configurations here" />
        <Space h="xl" />
        <Box style={{ textAlign: "center", fontWeight:"bolder" }}>
            You need an auto-setup script to run!! In the future will be available a setup wizard on this page.
        </Box>
    </Container>
}