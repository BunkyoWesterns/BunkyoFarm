import { useTokenStore } from "./stores"


export const DEV_IP_BACKEND = "127.0.0.1:5050"

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