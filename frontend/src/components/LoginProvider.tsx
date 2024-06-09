import { postFormRequest } from "@/utils/net";
import { statusQuery } from "@/utils/queries";
import { useGlobalStore, useTokenStore } from "@/utils/stores";
import { Box, Button, Group, PasswordInput, Space } from "@mantine/core"
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications'
import { useEffect } from "react";
import { SetupScreen } from "@/components/SetupScreen";
import { WelcomeTitle } from "@/components/WelcomeTitle";

export const LoginProvider = ({ children }: { children:any }) => {

    const [token, setToken] = useTokenStore((store) => [store.loginToken, store.setToken])
    const [loadingStatus, setLoading] = useGlobalStore((store) => [store.loading, store.setLoader])
    const status = statusQuery()
    
    const form = useForm({
        initialValues: {
            password: '',
        },
        validate: {
            password: (val) => val == ""? "Password is required" : null,
        },
    });
    
    useEffect(() => {
        setLoading(false)
        form.reset()
    },[token])


    if (status.data?.status == "setup"){
        return <SetupScreen />
    }

    if (status.data?.loggined){
        return <>{children}</>
    }

    return <Box className="center-flex-col" style={{
        width: "100%",
        height: "100%",
    }}>
        <WelcomeTitle description="A password is required to access to the platform!" />
        <Space h="md" />
        <form
            style={{
                width: "80%"
            }} 
            onSubmit={form.onSubmit((values) => {
            setLoading(true)
            postFormRequest("login", {body: {username: "web-user", ...values}})
            .then( (res) => {
                if(res.access_token){
                    setToken(res.access_token)
                    status.refetch()
                }else{
                    notifications.show({
                        title: "Unexpected Error",
                        message: res.detail??res??"Unknown error",
                        color: "red",
                        autoClose: 5000
                    })
                }
            })
            .catch( (err) => {
                notifications.show({
                    title: "Something went wrong!",
                    message: err.message??"Unknown error",
                    color: "red",
                    autoClose: 5000
                })
            })
            .finally(()=>{
                setLoading(false)
            })
        })}>
            <PasswordInput 
                withAsterisk
                label="Password"
                placeholder="Access Password"
                required
                {...form.getInputProps("password")}
            />
            <Space h="md" />
            <Group justify="flex-end" mt="md">
                <Button type="submit" loading={loadingStatus}>Login</Button>
            </Group>
        </form>
    </Box>
}