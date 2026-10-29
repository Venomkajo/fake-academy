import { UserPublic } from "../../api/auth"
import { fetchUserById } from "../../api/admin"

import { useParams } from "react-router-dom"
import { useQuery } from "@tanstack/react-query";

export default function EditUserPage() {

    const { id } = useParams<{ id: string }>();

    const userQuery = useQuery({
        queryKey: ['admin_user', id],
        queryFn: () => fetchUserById(Number(id)),
    })

  return (
    <section>
      <h1>Użytkownik {userQuery.data?.first_name} {userQuery.data?.last_name}:</h1>
        <p>Imię: {userQuery.data?.first_name}</p>
        <p>Nazwisko: {userQuery.data?.last_name}</p>
        <p>Email: {userQuery.data?.email}</p>
        <p>Rola: {userQuery.data?.role}</p>
        <p>Active: {userQuery.data?.is_active ? 'Tak' : 'Nie'}</p>
    </section>
  )
}