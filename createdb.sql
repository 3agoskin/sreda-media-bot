create table command_start(
    id integer primary key,
    created datetime,
    tg_user_id integer,
    tg_username varchar(255),
    tg_firstname varchar(255),
    come_from text
);

create table survey_new_year_tree(
    id integer primary key,
    created datetime,
    tg_user_id integer,
    city text,
    witch_tree text,
    why_this_choise text,
    where_bought text,
    when_bought text,
    which_eco text,
    why_eco text,
    result_survey text,
    result_survey_opinion text,
    user_phone text
);

create table postcard(
    id integer primary key,
    from_tg_user_id integer,
    to_tg_user_id integer,
    from_tg_user_username text,
    from_tg_user_name text,
    postcard_text text,
    show_author boolean,
    send boolean
);