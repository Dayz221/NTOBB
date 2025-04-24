import { Link, useNavigate } from "react-router-dom"
import "./adminpage.css"
import { useDispatch, useSelector } from "react-redux"
import { useEffect, useState } from "react"
import API from "../../utils/api"
import { setUser } from "../../redux/slice"

function Preloader() {
    return (
        <div className="preloader__container">
            <div id="preloader" className="visible"></div>
        </div>
    )
}

export default () => {
    const navigate = useNavigate()
    const dispatch = useDispatch()

    const user = useSelector(state => state.user)
    const [loadingState, setLoadingState] = useState(0)
    const [users, setUsers] = useState([])
    const [buildings, setBuildings] = useState([
        {
            id: "234567890-09876543",
            building_id: 0,
            water_bound: 0,
            mode3_enabled: false,
            pump_states: []
        },
    ])


    const signout = () => {
        localStorage.removeItem("token")
        navigate("/login")
    }

    const getMe = () => {
        API
            .get("/auth/me")
            .then((res) => {
                if (res.data.user.permissions < 2) {
                    navigate("/")
                } else {
                    dispatch(setUser(res.data.user))
                }
            })
            .catch((err) => {
                console.log(err)
                navigate("/login")
            })
    }

    useEffect(() => {
        setLoadingState(0)
        API
            .get("/auth/me")
            .then((res) => {
                if (res.data.user.permissions < 2) {
                    navigate("/")
                } else {
                    dispatch(setUser(res.data.user))
                }
            })
            .catch((err) => {
                console.log(err)
                navigate("/login")
            })
            .finally(() => setLoadingState(prev => prev + 1))

        API
            .get("/admin/users")
            .then((res) => {
                setUsers(res.data.users)
            })
            .catch((err) => {
                console.log(err)
            })
            .finally(() => setLoadingState(prev => prev + 1))

        API
            .get("/admin/buildings")
            .then((res) => {
                setBuildings(res.data.buildings)
            })
            .catch((err) => {
                console.log(err)
            })
            .finally(() => setLoadingState(prev => prev + 1))


        const intervalId = setInterval(getMe, 4000)

        return () => clearInterval(intervalId)
    }, [])


    if (loadingState < 3)
        return <Preloader />


    return (
        <div className="admin_page">
            <header className="user_page_header">
                <div className="width__container">
                    <div className="left_side">
                        <button className="button dark sign_out" onClick={signout}>
                            <div className="icon__container">
                                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path fillRule="evenodd" clipRule="evenodd" d="M8.37905 2.66859L12.0686 2.08881C15.2892 1.58272 16.8995 1.32967 17.9497 2.22779C19 3.12591 19 4.75596 19 8.01607V10.9996H13.0806L15.7809 7.62428L14.2191 6.37489L10.2191 11.3749L9.71938 11.9996L10.2191 12.6243L14.2191 17.6243L15.7809 16.3749L13.0806 12.9996H19V15.9831C19 19.2432 19 20.8733 17.9497 21.7714C16.8995 22.6695 15.2892 22.4165 12.0686 21.9104L8.37905 21.3306C6.76632 21.0771 5.95995 20.9504 5.47998 20.3891C5 19.8279 5 19.0116 5 17.3791V6.6201C5 4.98758 5 4.17132 5.47998 3.61003C5.95995 3.04874 6.76632 2.92202 8.37905 2.66859Z" fill="#222222" />
                                </svg>
                            </div>
                            <div className="button__text">Выйти</div>
                        </button>
                        <Link to="/">
                            <button className="button dark goto_admin">
                                <div className="icon__container">
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M19.6515 19.4054C20.2043 19.2902 20.5336 18.7117 20.2589 18.2183C19.6533 17.1307 18.6993 16.1749 17.4788 15.4465C15.907 14.5085 13.9812 14 12 14C10.0188 14 8.09292 14.5085 6.52112 15.4465C5.30069 16.1749 4.34666 17.1307 3.74108 18.2183C3.46638 18.7117 3.79562 19.2902 4.34843 19.4054C9.39524 20.4572 14.6047 20.4572 19.6515 19.4054Z" fill="#222222" />
                                        <circle cx="12" cy="8" r="5" fill="#222222" />
                                    </svg>
                                </div>
                                <div className="button__text">Юзер-панель</div>
                            </button>
                        </Link>
                    </div>

                    <div className="user_info__container">
                        <div className="username">{user.username}</div>
                        <div className="user_role">{(user.permissions > 1) ? "Admin" : "User"}</div>
                    </div>
                </div>
            </header>

            <div className="width__container column">
                <h1 className="select_user__title">Список пользователей:</h1>
                <div className="users_list">
                    {users.length == 0 ?
                        <div className="null_users_notification">
                            <div className="header_text">В системе не зарегистрировано ни одного пользователя!</div>
                            <div className="footer_text">Когда пользователи зарегистрируются, они покажатся тут.</div>
                        </div>
                        :
                        <>
                            {
                                users.map(el => {
                                    return (
                                        <div className="user_ainfo__container" key={el.id}>
                                            <div className="user_login_and_role">
                                                <div className="user_login_text">{el.email}</div>
                                                <div className="user_role_text">{el.permissions > 1 ? "Admin" : "User"}</div>
                                            </div>

                                            <div className="right_side">
                                                <div className="user_address">
                                                    <div className="address__title">Дом:</div>
                                                    <div className="address_val">{el.building_id}</div>
                                                </div>

                                                <div className="user_address">
                                                    <div className="address__title">Квартира: </div>
                                                    <div className="address_val">{el.building_id}</div>
                                                </div>

                                                <Link to={`/admin/${el.id}`}>
                                                    <button className="edit_user">
                                                        <div className="icon__container">
                                                            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                                                <path fillRule="evenodd" clipRule="evenodd" d="M17.204 10.796L19 9C19.5453 8.45475 19.8179 8.18213 19.9636 7.88803C20.2409 7.32848 20.2409 6.67152 19.9636 6.11197C19.8179 5.81788 19.5453 5.54525 19 5C18.4548 4.45475 18.1821 4.18213 17.888 4.03639C17.3285 3.75911 16.6715 3.75911 16.112 4.03639C15.8179 4.18213 15.5453 4.45475 15 5L13.1814 6.81866C14.1452 8.46926 15.5314 9.84482 17.204 10.796ZM11.7269 8.27311L4.8564 15.1436C4.43134 15.5687 4.21881 15.7812 4.07907 16.0423C3.93934 16.3034 3.88039 16.5981 3.7625 17.1876L3.1471 20.2646C3.08058 20.5972 3.04732 20.7635 3.14193 20.8581C3.23654 20.9527 3.40284 20.9194 3.73545 20.8529L6.81243 20.2375C7.40189 20.1196 7.69661 20.0607 7.95771 19.9209C8.21881 19.7812 8.43134 19.5687 8.8564 19.1436L15.7458 12.2542C14.1241 11.2386 12.7524 9.87627 11.7269 8.27311Z" />
                                                            </svg>
                                                        </div>
                                                        <div className="edit_user__text">Редактировать</div>
                                                    </button>
                                                </Link>
                                            </div>
                                        </div>
                                    )
                                })
                            }
                        </>
                    }
                </div>

                <h1 className="homes_controller__title">Список домов:</h1>
                <div className="homes_list">
                    {
                        buildings.map(el => {
                            return (
                                ""
                            )
                        })
                    }
                </div>
            </div>
        </div>
    )
}