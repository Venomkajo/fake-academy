import { fetchAllUsers } from '../../api/admin'

import { useQuery } from '@tanstack/react-query'

import EditUserButton from '../../components/admin/EditUserButton'

export default function AdminUsersPage(){

  const usersQuery = useQuery({
    queryKey: ['admin_users'],
    queryFn: fetchAllUsers,
  })

  return (
    <section>
      <h1>Lista użytkowników</h1>
      <p>{usersQuery.data?.length} użytkowników</p>
      <div>
        {usersQuery.data?.map((user: Awaited<ReturnType<typeof fetchAllUsers>>[number]) => (
          <div key={user.email}>
            {user.first_name} {user.last_name} ({user.email}) — {user.role} <EditUserButton user_id={user.id} />
          </div>
        ))}
      </div>
    </section>
  )
}
