import { useTokenStore } from "./stores"
import io from 'socket.io-client';

export const DEV_IP_BACKEND = "127.0.0.1:5050"

export const socket_io = import.meta.env.DEV?
    io("ws://"+DEV_IP_BACKEND, {
        path:"/sock/socket.io",
        transports: ['websocket'],
        auth: {
            token: useTokenStore.getState().loginToken
        }
    }):
    io({
        path:"/sock/socket.io",
        transports: ['websocket'],
        auth: {
            token: useTokenStore.getState().loginToken
        }
    })

export const SOCKET_IO_CHANNELS = [
    "client",
    "attack_group",
    "exploit",
    "service",
    "team",
    "attack_execution",
    "exploit_source",
    "submitter",
    "stats",
    "config"
]

export const DEBOUNCED_SOCKET_IO_CHANNELS = [
    "attack_execution",
    "stats",
]

export const sockIoChannelToQueryKeys = (channel:string):string[][] => {
    switch (channel) {
        case "client":
            return [
                ["clients"]
            ]
        case "attack_group":
            return [
                ["attacks"]
            ]
        case "exploit":
            return [
                ["exploits"]
            ]
        case "service":
            return [
                ["status"]
            ]
        case "team":
            return [
                ["status"]
            ]
        case "attack_execution":
            return [
                ["attacks"],
                ["flags"],
            ]
        case "exploit_source":
            return [
                ["exploits", "sources"]
            ]
        case "submitter":
            return [
                ["submitters"]
            ]
        case "stats":
            return [
                ["stats"]
            ]
        case "config":
            return [
                ["status"]
            ]
        default:
            return [
                [channel]
            ]
    }
}

export const getAuthHeaders = ():({[k:string]:string}) => {
    
    const token = useTokenStore.getState().loginToken
    if (!token){
        return {}
    }
    return {
        "Authorization": "Bearer "+token
    }

}

export const getLink = (url:string, params?: {[p:string]:any}): string => {
    url = url.trim()
    if (url.charAt(0) != '/'){
        url = "/"+url
    }
    let postfix = ""
    //removing from params undefined
    if (params){
        Object.keys(params).forEach((key) => {
            if (params[key] == null){
                delete params[key]
            }
        })
    }
    if (params){
        postfix = "?"
        postfix += new URLSearchParams(params).toString()
    }
    if (import.meta.env.DEV){
        return `http://${DEV_IP_BACKEND}/api`+url+postfix
    }
    return "/api"+url+postfix
}

export const elaborateJsonRequest = async (res: Response) => {
    if (res.status === 401){
        useTokenStore.getState().setToken(null)
        window.location.reload() // Unauthorized
    }
    if (!res.ok){
        return res.json().then( res => {throw res} )
    }
    return await res.json()
}

export const getRequest = async (url:string, options: {params?: {[p:string]:any}} = {}) => {
    return await fetch(getLink(url, options.params), {
        method: "GET",
        credentials: "same-origin",
        cache: 'no-cache',
        headers: {...getAuthHeaders()}
    }).then(elaborateJsonRequest)
}

export const postRequest = async (url:string, options: {params?: {[p:string]:any}, body?: {[p:string]:any}} = {}) => {
    return await fetch(getLink(url, options.params), {
        method: "POST",
        credentials: "same-origin",
        cache: 'no-cache',
        body: options.body?JSON.stringify(options.body):undefined,
        headers:{
            "Content-Type": "application/json",
            ...getAuthHeaders()
        }
    }).then(elaborateJsonRequest)
}

export const postFormRequest = async (url:string, options: {params?: {[p:string]:any}, body?: {[p:string]:any}} = {}):Promise<any> => {
    return await fetch(getLink(url, options.params), {
        method: "POST",
        credentials: "same-origin",
        cache: 'no-cache',
        body: options.body?new URLSearchParams(options.body).toString():undefined,
        headers:{
            "Content-Type": "application/x-www-form-urlencoded",
            ...getAuthHeaders()
        }
    }).then(elaborateJsonRequest)
}

export const putRequest = async (url:string, options: {params?: {[p:string]:any}, body?: {[p:string]:any}} = {}) => {
    return await fetch(getLink(url, options.params), {
        method: "PUT",
        credentials: "same-origin",
        cache: 'no-cache',
        body: options.body?JSON.stringify(options.body):undefined,
        headers:{
            "Content-Type": "application/json",
            ...getAuthHeaders()
        }
    }).then(elaborateJsonRequest)
}

export const deleteRequest = async (url:string, options: {params?: {[p:string]:any}} = {}) => {
    return await fetch(getLink(url, options.params), {
        method: "DELETE",
        credentials: "same-origin",
        cache: 'no-cache',
        headers:{...getAuthHeaders()}
    }).then(elaborateJsonRequest)
}