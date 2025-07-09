from copy import deepcopy


class GeneralPipeline:
    @classmethod
    def paginated_pipeline(cls, pg_no, pg_sz, count="totalCount", results="paginatedResults"):
        """
        同时查询分页后的数据后分页前的总数的一般通用pipeline，如果和其他pipeline组合，这部分应该放在最后面：
        other_pipeline.extend(paginated_pipeline(1, 10))

        Parameters
        ----------
        pg_no: int, 页号
        pg_sz: int,一页最多的数据条数
        count: str, 总数别名
        results: str, 详细结果的别名

        Notes
        -------
        # 查询后得到的结果格式
        [
            {
                'paginatedResults': [{document1}, {document2}, ...],
                'totalCount': [{'count': 100}]
            }
        ]
        # 空数据：
        [
            {'paginatedResults': [], 'totalCount': []}
        ]
        # 取值
        query_result = await PressureTestTaskModel.collection.aggregate(ppl).to_list(None)
        query_result = query_result[0]
        paginated_results = query_result["paginatedResults"]
        total_count = query_result["totalCount"][0]["count"] if paginated_results else 0
        """
        pg_no = int(pg_no or 0)
        pg_sz = int(pg_sz or 10000)
        pipeline = [
            {
                "$facet": {
                    count: [{"$count": "count"}],
                    results: [
                        {"$skip": max((pg_no - 1) * pg_sz, 0)},
                        {
                            "$limit": max(pg_sz, 1),
                        },
                    ],
                }
            },
        ]
        return pipeline

    @classmethod
    def datetime_fields_to_str_format(cls, *datetime_keys, fmt="%Y-%m-%d %H:%M:%S"):
        """将datetime类型的字段转成字符串类型，避免json序列化失败，建议在project阶段之前使用"""
        pipeline_stage = {
            "$addFields": {
                key: {
                    "$dateToString": {
                        "format": fmt,
                        "date": f"${key}",
                    }
                }
                for key in datetime_keys
            }
        }
        return pipeline_stage

    @classmethod
    def fields_range_match(cls, *range_criteria):
        """筛选小于等于~大于等于的范围，例如[1, 100], [None, 0.3]，左右都是闭区间"""
        match = {}
        for field, range_criterion in range_criteria:
            if not range_criterion:
                continue
            less, great = range_criterion[0], range_criterion[1]
            match.update(
                {
                    field: {
                        **({"$gte": less} if less is not None else {}),
                        **({"$lte": great} if great is not None else {}),
                    }
                }
            )
        return match

    @classmethod
    def pagination_count_pipeline(cls, pipeline, pg_no, pg_sz):
        ppl_count = deepcopy(pipeline)
        ppl_count.append({"$count": "count"})
        pg_no = int(pg_no or 0)
        pg_sz = int(pg_sz or 10000)
        pipeline.extend(
            [
                {"$skip": max((pg_no - 1) * pg_sz, 0)},
                {
                    "$limit": max(pg_sz, 1),
                },

            ]
        )
        return pipeline, ppl_count
