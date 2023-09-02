from models.connection import DBConnection
from utils.types import OrgType, RolesType

db = DBConnection()


def fetch_queries(muid):
    query = """
        SELECT
            user.mu_id,
            user.first_name,
            user.last_name,
            user.profile_pic,
            role.title AS role,
            total_karma.karma,
            interest_group.name AS interest_group_name,
            socials.github,
            organization.code AS organization_code,
            organization.org_type AS org_type
        FROM
            user
        LEFT JOIN total_karma ON user.id = total_karma.user_id
        LEFT JOIN user_ig_link ON user.id = user_ig_link.user_id
        LEFT JOIN interest_group ON user_ig_link.ig_id = interest_group.id
        LEFT JOIN user_role_link ON user_role_link.user_id = user.id
        LEFT JOIN role ON role.id = user_role_link.role_id
        LEFT JOIN socials ON user.id = socials.user_id
        LEFT JOIN user_organization_link ON user.id = user_organization_link.user_id
        LEFT JOIN organization ON user_organization_link.org_id = organization.id and org_type = :org_type
        WHERE user.mu_id = :mu_id;
    """
    user_data = db.fetch_all_data(query, params={'mu_id': muid, 'org_type': OrgType.COLLEGE.value})

    if user_data:
        data = {
            "mu_id": f"{user_data[0][0]}",
            "name": f"{user_data[0][1]} {user_data[0][2]}" if user_data[0][2] else user_data[0][1],
            "profile_pic": user_data[0][3],
            "karma": str(user_data[0][5]),
            "github_username": user_data[0][7],
            "org_code": list(set([row[8] for row in user_data if row[8]])),
            "roles": list(set([row[4] for row in user_data if row[4]])),
            "ig_name": list(set([row[6] for row in user_data if row[6]])),
            'org_types': list(set([row[9] for row in user_data if row[9]]))
        }
    else:
        return None

    main_role = next((role for role in data["roles"] if
                      role in [RolesType.STUDENT.value, RolesType.MENTOR.value, RolesType.ENABLER.value]),
                     RolesType.MULEARNER.value)

    if main_role in [RolesType.MENTOR.value, RolesType.ENABLER.value]:
        rank_query = """
            SELECT total_karma.karma, user.mu_id
            FROM total_karma
            INNER JOIN user_role_link ON user_role_link.user_id = total_karma.user_id
            INNER JOIN role ON role.id = user_role_link.role_id
            INNER JOIN user ON user.id = total_karma.user_id
            WHERE role.title = :title
            ORDER BY total_karma.karma DESC;

        """
        params = {'title': main_role}
    else:
        rank_query = """
            SELECT total_karma.karma, user.mu_id
            FROM total_karma
            LEFT JOIN (
                SELECT user_role_link.user_id
                FROM user_role_link
                INNER JOIN role ON role.id = user_role_link.role_id
                GROUP BY user_role_link.user_id
                HAVING SUM(IF(role.title IN (:mentor, :enabler), 1, 0)) = 0
            ) AS users ON total_karma.user_id = users.user_id
            INNER JOIN user ON total_karma.user_id = user.id
            ORDER BY total_karma.karma DESC;

        """
        params = {'enabler': RolesType.ENABLER.value, "mentor": RolesType.MENTOR.value}

    rank_list = db.fetch_all_data(rank_query, params)

    count = 0
    for x in rank_list:
        count += 1
        if x[1] == data["mu_id"]:
            data["rank"] = count
            data["score"] = int(x[0])
            data["main_role"] = main_role

    return data
