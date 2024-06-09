import { Box, Image, Title } from "@mantine/core"

export const WelcomeTitle = (
    { title, description, showAnimation }:
    { title?: string, description?: string, showAnimation?:boolean}) => {
    return <Box className="center-flex-col">
        <Box className="center-flex">
            <Title order={1} style={{
                textAlign: "center",
                zIndex:1
            }}>
                {title??"Welcome to ExploitFarm"}             
            </Title>
            <Image src="/logo.png" alt="ExploitFarm Logo" width={70} height={70} style={{marginLeft:5}}/> 
        </Box>
        

        <Title order={3} style={{
            textAlign: "center",
            zIndex:1
        }}>
            {description??<>The attack manager and flag submitter by <a href="https://pwnzer0tt1.it" target="_blank">Pwnzer0tt1</a></>}
        </Title>

        { (showAnimation??true)?
        <video loop style={{
            marginTop: -40,
            marginBottom: -40,
            maxHeight: 300,
            zIndex:0
        }} autoPlay muted>
            <source src="/xfarm-animation.webm" type="video/webm"></source>
        </video>:null}

    </Box>
}